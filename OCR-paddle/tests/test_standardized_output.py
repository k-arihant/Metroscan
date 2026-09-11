"""
Comprehensive Test Suite for Standardized Output & Rule 7 Legal Metrology Compliance:
1. Schema Validation (valid output, missing top-level keys, missing detection keys, invalid enum, invalid data type)
2. Detection Structure (verify all required detection keys exist)
3. Physical Calculation (pixels_per_mm=20, height_px=40 -> height_mm=2.0)
4. Missing Calibration (UNABLE_TO_VERIFY and physical mm values null)
5. Rule 7 Area Thresholds (50, 50+, 100, 100+, 500, 500+, 2500, 2500+; specifically 120 cm² -> 2.5 mm normal / 4.0 mm blown)
6. Width/Height Ratio (ratio > 1/3, ratio = 1/3, ratio < 1/3; equality passes)
7. Narrow Character Exceptions ('1', 'i', 'I', 'l' do not fail solely because of ratio)
8. Karachi Bakery Regression Fixture (19 detections, two-column structure, misaligned row association, traceability)
"""
import unittest
import numpy as np

from src.utils.geometry import BoundingBox
from src.extraction.tokens import CanonicalToken, OCRTokenStore
from src.compliance.rule_7 import (
    get_rule_7_threshold,
    evaluate_rule_7_for_detection,
    summarize_rule_7_compliance,
    STATUS_COMPLIANT,
    STATUS_NON_COMPLIANT,
    STATUS_UNABLE_TO_VERIFY,
    VERIFICATION_VERIFIED,
)
from src.compliance.font_metrics import measure_font_metrics, FontMetrics
from src.output.schema import (
    validate_output_schema,
    validate_or_raise,
    SchemaValidationError,
    VALID_DETECTION_TYPES,
    VALID_RULE_7_STATUSES,
)
from src.output.builder import (
    build_standardized_output,
    classify_detection_type,
    find_matching_detection_id,
)
from src.extraction.field_extractor import extract_all_fields


class TestSchemaValidation(unittest.TestCase):
    """Test standardized JSON schema validation and error raising."""

    def setUp(self):
        # Create a valid minimal standardized output dictionary
        self.valid_data = {
            "package_id": "pkg_test_01",
            "processing": {
                "pipeline_version": "3.0",
                "timestamp": "2026-09-08T20:00:00",
                "ocr_status": "success",
            },
            "images": [
                {
                    "image_id": "img_test_01",
                    "filename": "test.jpeg",
                    "label_side": "back",
                    "width": 1200,
                    "height": 800,
                    "image_quality": {
                        "quality_score": 0.95,
                        "blur_score": 0.90,
                        "resolution_sufficient": True,
                        "orientation_corrected": False,
                        "deskew_applied": False,
                    },
                    "calibration": {
                        "available": True,
                        "pixels_per_mm": 20.0,
                        "source": "fiducial",
                        "confidence": 0.99,
                    },
                    "principal_display_panel": {
                        "detected": True,
                        "width_px": 800.0,
                        "height_px": 600.0,
                        "width_cm": 4.0,
                        "height_cm": 3.0,
                        "area_cm2": 12.0,
                        "measurement_source": "manual",
                        "confidence": 0.95,
                    },
                }
            ],
            "detections": [
                {
                    "detection_id": "det_001",
                    "source_image_id": "img_test_01",
                    "text": "MRP Rs. 220.00",
                    "normalized_text": "MRP Rs. 220.00",
                    "confidence": 0.95,
                    "ocr_metadata": {
                        "engine": "paddle",
                        "pass": "primary",
                        "preprocessing": "original",
                        "source": "ocr",
                    },
                    "detection_type": "mixed",
                    "bounding_box": {"x": 100, "y": 200, "width": 300, "height": 40},
                    "layout": {"column": 1, "row": 1, "role": "value", "layout_confidence": 0.92},
                    "field": {"predicted": "mrp", "candidate": True, "field_confidence": 0.95},
                    "font_metrics": {
                        "measurement_available": True,
                        "character_height_px": 30,
                        "character_widths_px": [15, 16, 15],
                        "minimum_character_width_px": 15,
                        "width_height_ratio": 0.50,
                        "measurement_confidence": 0.90,
                    },
                    "physical_metrics": {
                        "measurement_available": True,
                        "character_height_mm": 1.50,
                        "minimum_character_width_mm": 0.75,
                    },
                    "rule_7": {
                        "applicable": True,
                        "verification_status": "VERIFIED",
                        "required_character_height_mm": 1.0,
                        "measured_character_height_mm": 1.50,
                        "height_status": "COMPLIANT",
                        "minimum_width_height_ratio": 0.3333333333333333,
                        "measured_width_height_ratio": 0.50,
                        "width_status": "COMPLIANT",
                        "overall_status": "COMPLIANT",
                        "confidence": 0.92,
                        "reason": None,
                    },
                }
            ],
            "extracted_fields": {
                "product_name": None,
                "manufacturer": None,
                "manufacturer_address": None,
                "net_quantity": None,
                "mrp": {
                    "value": "220.00",
                    "currency": "INR",
                    "source_detection_id": "det_001",
                    "confidence": 0.95,
                },
                "unit_sale_price": None,
                "packed_on": None,
                "use_by_date": None,
                "batch_lot_number": None,
                "fssai_license": None,
                "country_of_origin": None,
            },
            "compliance_summary": {
                "verified": 1,
                "compliant": 1,
                "non_compliant": 0,
                "unable_to_verify": 0,
                "rule_7": {
                    "status": "COMPLIANT",
                    "verified": 1,
                    "compliant": 1,
                    "non_compliant": 0,
                    "unable_to_verify": 0,
                    "detections_evaluated": 1,
                    "detections_compliant": 1,
                    "detections_non_compliant": 0,
                    "detections_unable_to_verify": 0,
                },
            },
        }

    def test_valid_schema_passes(self):
        """A valid standardized dictionary passes validation without errors."""
        is_valid, errors = validate_output_schema(self.valid_data)
        self.assertTrue(is_valid, f"Expected valid schema, got errors: {errors}")
        self.assertEqual(len(errors), 0)
        # Should not raise exception
        validate_or_raise(self.valid_data)

    def test_missing_required_top_level_key(self):
        """Missing top-level key must be caught with an informative error."""
        invalid_data = dict(self.valid_data)
        del invalid_data["compliance_summary"]

        is_valid, errors = validate_output_schema(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("compliance_summary" in e for e in errors))

        with self.assertRaises(SchemaValidationError) as ctx:
            validate_or_raise(invalid_data)
        self.assertIn("compliance_summary", str(ctx.exception))

    def test_missing_required_detection_key(self):
        """Missing required key inside a detection must be reported."""
        invalid_data = dict(self.valid_data)
        bad_det = dict(invalid_data["detections"][0])
        del bad_det["font_metrics"]
        invalid_data["detections"] = [bad_det]

        is_valid, errors = validate_output_schema(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("font_metrics" in e for e in errors))

    def test_invalid_enum_rejected(self):
        """Invalid detection_type or rule_7 overall_status must fail schema validation."""
        # Test bad detection type
        bad_data = dict(self.valid_data)
        bad_det = dict(bad_data["detections"][0])
        bad_det["detection_type"] = "hyperlink"  # Not in enum
        bad_data["detections"] = [bad_det]

        is_valid, errors = validate_output_schema(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("invalid detection_type" in e for e in errors))

        # Test bad rule 7 status
        bad_det2 = dict(self.valid_data["detections"][0])
        bad_det2["rule_7"] = dict(bad_det2["rule_7"])
        bad_det2["rule_7"]["overall_status"] = "MAYBE_COMPLIANT"  # Not in enum
        bad_data["detections"] = [bad_det2]

        is_valid, errors = validate_output_schema(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("invalid rule_7.overall_status" in e for e in errors))

    def test_invalid_data_type_rejected(self):
        """Wrong types (e.g. string instead of dict for bounding_box) must fail validation."""
        bad_data = dict(self.valid_data)
        bad_det = dict(bad_data["detections"][0])
        bad_det["bounding_box"] = "x=100, y=200"  # String instead of dict
        bad_data["detections"] = [bad_det]

        is_valid, errors = validate_output_schema(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("bounding_box must be a dictionary" in e for e in errors))


class TestDetectionStructure(unittest.TestCase):
    """Verify detection object contains every required key and deterministic sequential IDs."""

    def test_all_detection_keys_present_in_builder(self):
        # Create a mock line
        line = CanonicalToken("NET WT. 400g", "net wt. 400g", BoundingBox(100, 100, 300, 140), 0.95, token_type="line")
        out = build_standardized_output(
            image_filename="test_pkg.jpeg",
            image=None,
            lines=[line],
            words=[line],
            validate=True,
        )

        self.assertEqual(len(out["detections"]), 1)
        det = out["detections"][0]

        expected_keys = [
            "detection_id",
            "source_image_id",
            "text",
            "normalized_text",
            "confidence",
            "ocr_metadata",
            "detection_type",
            "bounding_box",
            "layout",
            "field",
            "font_metrics",
            "physical_metrics",
            "rule_7",
        ]
        for key in expected_keys:
            self.assertIn(key, det, f"Required detection key '{key}' missing from builder output.")

        # Deterministic sequential ID format
        self.assertEqual(det["detection_id"], "det_001")


class TestPhysicalCalculation(unittest.TestCase):
    """Test physical millimetre calculations with calibration."""

    def test_exact_physical_calculation(self):
        """pixels_per_mm = 20, height_px = 40 must produce height_mm = 2.0."""
        eval_res = evaluate_rule_7_for_detection(
            text="TEST",
            character_height_px=40,
            minimum_character_width_px=20,
            width_height_ratio=0.50,
            measurement_available=True,
            pixels_per_mm=20.0,
            pdp_area_cm2=80.0,
            blown_formed_moulded=False,
        )

        self.assertEqual(eval_res.verification_status, VERIFICATION_VERIFIED)
        self.assertAlmostEqual(eval_res.measured_character_height_mm, 2.0, places=2)
        # Threshold for 80 cm² normal package is 1.5 mm. 2.0 >= 1.5 -> COMPLIANT
        self.assertEqual(eval_res.height_status, STATUS_COMPLIANT)
        self.assertEqual(eval_res.overall_status, STATUS_COMPLIANT)

    def test_missing_calibration_returns_unable_to_verify(self):
        """When calibration is missing or 0, physical measurements must be null and status UNABLE_TO_VERIFY."""
        eval_res = evaluate_rule_7_for_detection(
            text="TEST",
            character_height_px=40,
            minimum_character_width_px=20,
            width_height_ratio=0.50,
            measurement_available=True,
            pixels_per_mm=None,  # Missing calibration
            pdp_area_cm2=80.0,
        )

        self.assertEqual(eval_res.verification_status, STATUS_UNABLE_TO_VERIFY)
        self.assertEqual(eval_res.overall_status, STATUS_UNABLE_TO_VERIFY)
        self.assertIsNone(eval_res.measured_character_height_mm)
        self.assertIn("Physical calibration (pixels_per_mm) is unavailable", eval_res.reason)

    def test_missing_pdp_area_returns_unable_to_verify(self):
        """When PDP area is missing, Rule 7 cannot be verified."""
        eval_res = evaluate_rule_7_for_detection(
            text="TEST",
            character_height_px=40,
            minimum_character_width_px=20,
            width_height_ratio=0.50,
            measurement_available=True,
            pixels_per_mm=20.0,
            pdp_area_cm2=None,  # Missing PDP
        )

        self.assertEqual(eval_res.verification_status, STATUS_UNABLE_TO_VERIFY)
        self.assertEqual(eval_res.overall_status, STATUS_UNABLE_TO_VERIFY)
        self.assertIn("Principal Display Panel (PDP) area is unavailable", eval_res.reason)


class TestRule7AreaThresholds(unittest.TestCase):
    """Test Rule 7 area thresholds at and around every boundary (50, 100, 500, 2500 cm²)."""

    def test_boundary_50_cm2(self):
        # A <= 50 cm²: Normal = 1.0 mm, Blown = 2.0 mm
        norm_50, blown_50 = get_rule_7_threshold(50.0)
        self.assertEqual(norm_50, 1.0)
        self.assertEqual(blown_50, 2.0)

        # 50+ cm² (e.g. 50.01): Normal = 1.5 mm, Blown = 3.0 mm
        norm_50_plus, blown_50_plus = get_rule_7_threshold(50.01)
        self.assertEqual(norm_50_plus, 1.5)
        self.assertEqual(blown_50_plus, 3.0)

    def test_boundary_100_cm2(self):
        # 50 < A <= 100 cm²: Normal = 1.5 mm, Blown = 3.0 mm
        norm_100, blown_100 = get_rule_7_threshold(100.0)
        self.assertEqual(norm_100, 1.5)
        self.assertEqual(blown_100, 3.0)

        # 100+ cm² (e.g. 100.1): Normal = 2.5 mm, Blown = 4.0 mm
        norm_100_plus, blown_100_plus = get_rule_7_threshold(100.1)
        self.assertEqual(norm_100_plus, 2.5)
        self.assertEqual(blown_100_plus, 4.0)

    def test_specific_requirement_120_cm2(self):
        """Prompt requirement: Specifically verify 120 cm² -> 2.5 mm normal / 4.0 mm blown."""
        norm_120, blown_120 = get_rule_7_threshold(120.0)
        self.assertEqual(norm_120, 2.5)
        self.assertEqual(blown_120, 4.0)

    def test_boundary_500_cm2(self):
        # 100 < A <= 500 cm²: Normal = 2.5 mm, Blown = 4.0 mm
        norm_500, blown_500 = get_rule_7_threshold(500.0)
        self.assertEqual(norm_500, 2.5)
        self.assertEqual(blown_500, 4.0)

        # 500+ cm² (e.g. 500.5): Normal = 4.0 mm, Blown = 6.0 mm
        norm_500_plus, blown_500_plus = get_rule_7_threshold(500.5)
        self.assertEqual(norm_500_plus, 4.0)
        self.assertEqual(blown_500_plus, 6.0)

    def test_boundary_2500_cm2(self):
        # 500 < A <= 2500 cm²: Normal = 4.0 mm, Blown = 6.0 mm
        norm_2500, blown_2500 = get_rule_7_threshold(2500.0)
        self.assertEqual(norm_2500, 4.0)
        self.assertEqual(blown_2500, 6.0)

        # 2500+ cm² (e.g. 2501.0): Normal = 6.0 mm, Blown = 6.0 mm
        norm_2500_plus, blown_2500_plus = get_rule_7_threshold(2501.0)
        self.assertEqual(norm_2500_plus, 6.0)
        self.assertEqual(blown_2500_plus, 6.0)


class TestWidthHeightRatio(unittest.TestCase):
    """Test Rule 7(3) character width-to-height ratio requirement (ratio >= 1/3)."""

    def test_ratio_greater_than_one_third(self):
        """ratio > 1/3 must pass."""
        eval_res = evaluate_rule_7_for_detection(
            text="ABC",
            character_height_px=30,
            minimum_character_width_px=15,
            width_height_ratio=0.50,  # 0.50 > 1/3
            measurement_available=True,
            pixels_per_mm=10.0,
            pdp_area_cm2=40.0,
        )
        self.assertEqual(eval_res.width_status, STATUS_COMPLIANT)

    def test_ratio_exactly_equal_one_third(self):
        """ratio == 1/3 must pass (equality case)."""
        exact_one_third = 1.0 / 3.0
        eval_res = evaluate_rule_7_for_detection(
            text="ABC",
            character_height_px=30,
            minimum_character_width_px=10,
            width_height_ratio=exact_one_third,
            measurement_available=True,
            pixels_per_mm=10.0,
            pdp_area_cm2=40.0,
        )
        self.assertEqual(eval_res.width_status, STATUS_COMPLIANT)

    def test_ratio_less_than_one_third(self):
        """ratio < 1/3 must fail."""
        eval_res = evaluate_rule_7_for_detection(
            text="ABC",
            character_height_px=30,
            minimum_character_width_px=8,
            width_height_ratio=0.25,  # 0.25 < 1/3
            measurement_available=True,
            pixels_per_mm=10.0,
            pdp_area_cm2=40.0,
        )
        self.assertEqual(eval_res.width_status, STATUS_NON_COMPLIANT)
        self.assertEqual(eval_res.overall_status, STATUS_NON_COMPLIANT)


class TestNarrowCharacterExceptions(unittest.TestCase):
    """Test narrow character exceptions: '1', 'i', 'I', 'l' must not fail solely due to ratio."""

    def test_narrow_characters_exempt(self):
        for narrow_char in ["1", "i", "I", "l"]:
            eval_res = evaluate_rule_7_for_detection(
                text=narrow_char,
                character_height_px=30,
                minimum_character_width_px=5,
                width_height_ratio=5.0 / 30.0,  # ~0.1667 < 0.333
                measurement_available=True,
                pixels_per_mm=10.0,  # 30px / 10 = 3.0mm >= 1.0mm
                pdp_area_cm2=40.0,
            )
            self.assertEqual(
                eval_res.width_status,
                STATUS_COMPLIANT,
                f"Narrow character '{narrow_char}' should be exempt from ratio failure.",
            )
            self.assertEqual(eval_res.overall_status, STATUS_COMPLIANT)

    def test_non_exempt_narrow_fails(self):
        """Non-exempt characters (like 'J' or 'T') with narrow ratio must fail."""
        eval_res = evaluate_rule_7_for_detection(
            text="J",
            character_height_px=30,
            minimum_character_width_px=5,
            width_height_ratio=5.0 / 30.0,
            measurement_available=True,
            pixels_per_mm=10.0,
            pdp_area_cm2=40.0,
        )
        self.assertEqual(eval_res.width_status, STATUS_NON_COMPLIANT)
        self.assertEqual(eval_res.overall_status, STATUS_NON_COMPLIANT)


class TestCountryOfOriginExtraction(unittest.TestCase):
    """Verify country-of-origin extraction patterns."""

    def test_product_of_india(self):
        from src.extraction import patterns
        text = "STORE IN COOL DRY PLACE. PRODUCT OF INDIA. BATCH NO: 123"
        ext = patterns.extract_country_of_origin(text)
        self.assertIsNotNone(ext)
        self.assertEqual(ext[0], "India")

    def test_made_in_india(self):
        from src.extraction import patterns
        text = "Made in India"
        ext = patterns.extract_country_of_origin(text)
        self.assertIsNotNone(ext)
        self.assertEqual(ext[0], "India")

    def test_country_of_origin_explicit(self):
        from src.extraction import patterns
        text = "Country of Origin: India"
        ext = patterns.extract_country_of_origin(text)
        self.assertIsNotNone(ext)
        self.assertEqual(ext[0], "India")


class TestKarachiBakeryRegressionFixture(unittest.TestCase):
    """
    Karachi Bakery Regression Test:
    Use the 19 detections fixture with two-column structure and misaligned rows.
    Verify:
      1. Detection count remains exactly 19.
      2. Two-column structure remains correct.
      3. Misaligned rows remain associated correctly.
      4. Source detection IDs remain traceable.
      5. Standardized output contains all expected detections.
    """

    def setUp(self):
        # 19 detections corresponding to the Karachi Bakery label
        # Headers / company / general text
        t1 = CanonicalToken("Karachi Bakery", "karachi bakery", BoundingBox(100, 80, 500, 130), 0.98, token_type="line")
        t2 = CanonicalToken("Fruit Biscuits", "fruit biscuits", BoundingBox(100, 140, 420, 185), 0.97, token_type="line")
        t3 = CanonicalToken("Ingredients: Wheat Flour, Sugar, Butter", "ingredients: wheat flour, sugar, butter", BoundingBox(100, 200, 800, 240), 0.95, token_type="line")
        t4 = CanonicalToken("Nutritional Information per 100g", "nutritional information per 100g", BoundingBox(100, 260, 600, 295), 0.94, token_type="line")
        t5 = CanonicalToken("Energy: 480 kcal, Protein: 6.2g", "energy: 480 kcal, protein: 6.2g", BoundingBox(100, 310, 580, 345), 0.92, token_type="line")
        t6 = CanonicalToken("Manufactured by: Karachi Bakery Pearl Pvt Ltd", "manufactured by: karachi bakery pearl pvt ltd", BoundingBox(100, 370, 850, 410), 0.96, token_type="line")
        t7 = CanonicalToken("PRODUCT OF INDIA", "product of india", BoundingBox(100, 430, 400, 465), 0.96, token_type="line")

        # Column 1 (Labels at x ~ 100) and Column 2 (Values at x ~ 450, with misaligned y coordinates)
        t8 = CanonicalToken("Net Qty:", "net qty:", BoundingBox(100, 500, 240, 535), 0.98, token_type="line")
        t9 = CanonicalToken("400 g", "400 g", BoundingBox(450, 506, 550, 538), 0.97, token_type="line")

        t10 = CanonicalToken("M.R.P. (Incl. of all taxes):", "m.r.p. (incl. of all taxes):", BoundingBox(100, 560, 400, 595), 0.98, token_type="line")
        t11 = CanonicalToken("₹ 220.00", "₹ 220.00", BoundingBox(450, 564, 580, 598), 0.97, token_type="line")

        t12 = CanonicalToken("USP Rs:", "usp rs:", BoundingBox(100, 620, 230, 655), 0.96, token_type="line")
        t13 = CanonicalToken("0.55/g", "0.55/g", BoundingBox(450, 625, 540, 658), 0.96, token_type="line")

        t14 = CanonicalToken("Packed On:", "packed on:", BoundingBox(100, 680, 260, 715), 0.97, token_type="line")
        t15 = CanonicalToken("26.AUG.2026", "26.aug.2026", BoundingBox(450, 686, 610, 718), 0.97, token_type="line")

        t16 = CanonicalToken("Use By Date:", "use by date:", BoundingBox(100, 740, 280, 775), 0.98, token_type="line")
        t17 = CanonicalToken("25.JAN.2027", "25.jan.2027", BoundingBox(450, 744, 610, 778), 0.98, token_type="line")

        t18 = CanonicalToken("Lot No:", "lot no:", BoundingBox(100, 800, 220, 835), 0.96, token_type="line")
        t19 = CanonicalToken("62H1 27KI", "62h1 27ki", BoundingBox(450, 805, 590, 838), 0.96, token_type="line")

        self.tokens_19 = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18, t19]

    def test_karachi_bakery_19_detections_pipeline(self):
        """Verify full standardized pipeline on Karachi Bakery 19-detection fixture."""
        self.assertEqual(len(self.tokens_19), 19)

        # 1. Run field extraction
        field_res = extract_all_fields(
            lines=self.tokens_19,
            words=self.tokens_19,
            image_filename="t2_karachi.jpeg",
        )

        # 2. Build authoritative standardized output
        out = build_standardized_output(
            image_filename="t2_karachi.jpeg",
            image=None,
            lines=self.tokens_19,
            words=self.tokens_19,
            field_result=field_res,
            layout_struct=field_res.get("layout"),
            calibration={"pixels_per_mm": 15.0, "source": "known_scale"},
            pdp={"area_cm2": 150.0},
            validate=True,
        )

        # 3. Verify exactly 19 detections exist in standardized output
        self.assertEqual(len(out["detections"]), 19)
        det_ids = [d["detection_id"] for d in out["detections"]]
        self.assertEqual(det_ids[0], "det_001")
        self.assertEqual(det_ids[-1], "det_019")

        # 4. Verify extracted fields and traceability
        extracted = out["extracted_fields"]
        self.assertIsNotNone(extracted["net_quantity"])
        self.assertEqual(extracted["net_quantity"]["value"], "400")
        self.assertIsNotNone(extracted["net_quantity"]["source_detection_id"])

        self.assertIsNotNone(extracted["mrp"])
        self.assertEqual(extracted["mrp"]["value"], "220.00")
        self.assertIsNotNone(extracted["mrp"]["source_detection_id"])

        self.assertIsNotNone(extracted["unit_sale_price"])
        self.assertIn("0.55", extracted["unit_sale_price"]["value"])
        self.assertIsNotNone(extracted["unit_sale_price"]["source_detection_id"])

        self.assertIsNotNone(extracted["country_of_origin"])
        self.assertEqual(extracted["country_of_origin"]["value"], "India")
        self.assertIsNotNone(extracted["country_of_origin"]["source_detection_id"])

        # 5. Verify Rule 7 summary roll-up
        summary = out["compliance_summary"]
        self.assertIn("rule_7", summary)
        r7 = summary["rule_7"]
        self.assertEqual(r7["detections_evaluated"], 19)


if __name__ == "__main__":
    unittest.main()
