"""
Unit tests for PaddleOCR Standard JSON Output Writer and Schema Validation.
"""
import unittest
import tempfile
import json
from pathlib import Path

from src.output.json_writer import build_ocr_json, save_ocr_json, validate_ocr_json
from src.ocr.paddle_engine import PaddleOCREngine


class TestPaddleJSONWriter(unittest.TestCase):
    def setUp(self):
        self.sample_detections = [
            {
                "text": "(DD). Karachi bakery Pearl Pvt Limited",
                "confidence": 0.9821,
                "bbox": {"x": 245, "y": 10, "width": 315, "height": 28},
            },
            {
                "text": "Survey No 240, Shed No.4, Pedamma Gadda",
                "confidence": 0.9754,
                "bbox": {"x": 245, "y": 38, "width": 381, "height": 89},
            },
        ]

    def test_build_ocr_json_structure(self):
        """Verify the exact required JSON structure and field names."""
        res = build_ocr_json(
            image_name_or_path="images/test.jpeg",
            width=1920,
            height=1440,
            detections=self.sample_detections,
        )

        # 1. Top-level keys
        self.assertEqual(res["package_id"], "pkg_test")
        self.assertEqual(len(res["images"]), 1)
        self.assertEqual(len(res["detections"]), 2)

        # 2. Image object
        img = res["images"][0]
        self.assertEqual(img["image_id"], "img_test")
        self.assertEqual(img["label_side"], "unknown")
        self.assertEqual(img["width"], 1920)
        self.assertEqual(img["height"], 1440)

        # 3. Detections
        det1 = res["detections"][0]
        self.assertEqual(det1["detection_id"], "det_001")
        self.assertEqual(det1["source_image_id"], "img_test")
        self.assertEqual(det1["text"], "(DD). Karachi bakery Pearl Pvt Limited")
        self.assertEqual(det1["confidence"], 0.9821)
        self.assertEqual(det1["bounding_box"], {"x": 245, "y": 10, "width": 315, "height": 28})

        det2 = res["detections"][1]
        self.assertEqual(det2["detection_id"], "det_002")
        self.assertEqual(det2["source_image_id"], "img_test")

        # 4. Schema validation
        is_valid, errors = validate_ocr_json(res)
        self.assertTrue(is_valid, f"Validation errors: {errors}")

    def test_custom_package_id_and_label_side(self):
        """Verify custom package_id and label_side are preserved when provided."""
        res = build_ocr_json(
            image_name_or_path="images/t2.jpeg",
            width=1000,
            height=800,
            detections=[],
            package_id="pkg_karachi_bakery_001",
            label_side="back",
        )
        self.assertEqual(res["package_id"], "pkg_karachi_bakery_001")
        self.assertEqual(res["images"][0]["label_side"], "back")
        self.assertEqual(res["detections"], [])

        is_valid, errors = validate_ocr_json(res)
        self.assertTrue(is_valid, f"Validation errors: {errors}")

    def test_empty_ocr_result_produces_valid_json(self):
        """Section 15: Empty OCR detections list must produce valid JSON."""
        res = build_ocr_json(
            image_name_or_path="images/blank.png",
            width=800,
            height=600,
            detections=[],
        )
        self.assertEqual(res["package_id"], "pkg_blank")
        self.assertEqual(res["detections"], [])
        is_valid, errors = validate_ocr_json(res)
        self.assertTrue(is_valid, f"Validation errors: {errors}")

    def test_save_ocr_json_naming_convention(self):
        """Section 10 & 28: Output file must be named <image_stem>_ocr.json in output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            res = build_ocr_json(
                image_name_or_path="images/sample_label.webp",
                width=100,
                height=100,
                detections=self.sample_detections,
            )
            saved_path = save_ocr_json(res, "images/sample_label.webp", output_dir=tmpdir)

            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.name, "sample_label_ocr.json")

            # Verify saved content matches
            with open(saved_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["package_id"], "pkg_sample_label")
            self.assertEqual(len(loaded["detections"]), 2)

    def test_polygon_to_bbox_conversion(self):
        """Section 8: 4-point polygon must convert to axis-aligned bounding box."""
        poly = [
            [245.0, 10.0],
            [560.0, 10.0],
            [560.0, 38.0],
            [245.0, 38.0],
        ]
        bbox = PaddleOCREngine.polygon_to_bbox(poly)
        self.assertEqual(bbox["x"], 245)
        self.assertEqual(bbox["y"], 10)
        self.assertEqual(bbox["width"], 315)
        self.assertEqual(bbox["height"], 28)

    def test_validation_catches_invalid_structure(self):
        """Ensure validator flags missing keys and invalid types."""
        bad_json = {
            "package_id": "",
            "images": [{"width": "not_a_number"}],
            "detections": [{"confidence": 1.5}],
        }
        is_valid, errors = validate_ocr_json(bad_json)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errors), 3)


if __name__ == "__main__":
    unittest.main()
