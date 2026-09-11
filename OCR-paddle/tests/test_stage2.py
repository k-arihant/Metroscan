"""
Unit Test Suite for Stage 2 OCR Upgrade:
- Dot-Matrix text recognition, blob analysis, multi-variant voting, and coordinate preservation
- Layout-aware label/value association, multi-word label grouping, scale-aware row detection
- Synthetic perturbed two-column regression test (Section 44 of requirements)
- Semantic safety filtering (rejecting cross-field mismatches like MFG -> price or MRP -> date)
"""
import unittest
import numpy as np

import config
from src.utils.geometry import BoundingBox
from src.extraction.tokens import CanonicalToken, OCRTokenStore
from src.extraction.candidate import FieldCandidate
from src.ocr.dot_matrix import (
    detect_dot_matrix_region,
    character_consensus_voting,
    normalize_confusable_characters,
    generate_dot_matrix_variants,
)
from src.extraction.layout_association import (
    group_multi_word_labels,
    classify_value_token,
    detect_columns_and_rows,
    score_label_value_pair,
    solve_global_assignment,
    analyze_label_layout,
    LabelEntity,
    ValueEntity,
)


class TestDotMatrixPipeline(unittest.TestCase):
    """Test dot-matrix detection, preprocessing variants, and character voting."""

    def test_synthetic_dot_matrix_detection(self):
        """Synthetic dot grid should be recognized as dot-matrix text."""
        img = np.ones((80, 200), dtype=np.uint8) * 255
        # Draw a regular grid of dots
        for r in range(15, 65, 8):
            for c in range(15, 185, 10):
                img[r : r + 3, c : c + 3] = 0

        report = detect_dot_matrix_region(img)
        self.assertTrue(report.is_dot_matrix)
        self.assertGreaterEqual(report.confidence, 0.50)
        self.assertGreater(report.component_count, 10)

    def test_solid_text_detection_is_not_dot_matrix(self):
        """Solid continuous blocks should NOT be flagged as dot-matrix."""
        img = np.ones((80, 200), dtype=np.uint8) * 255
        # Draw two large solid rectangles representing continuous strokes
        img[20:60, 20:90] = 0
        img[20:60, 110:180] = 0

        report = detect_dot_matrix_region(img)
        self.assertFalse(report.is_dot_matrix)

    def test_controlled_character_normalization(self):
        """Test field-specific character confusion normalization."""
        # Date context: O -> 0, G -> 6, B -> 8
        self.assertEqual(normalize_confusable_characters("06/O9/26", "date"), "06/09/26")
        self.assertEqual(normalize_confusable_characters("21/O3/2026", "date"), "21/03/2026")
        self.assertEqual(normalize_confusable_characters("16/11/2G", "date"), "16/11/26")

        # MRP context: OO -> .00 or 0
        self.assertEqual(normalize_confusable_characters("22 OO", "mrp"), "22.00")
        self.assertEqual(normalize_confusable_characters("36O.00", "mrp"), "360.00")

        # Batch context: DO NOT replace letters in alphanumeric codes
        self.assertEqual(normalize_confusable_characters("BATCH AB1234", "batch"), "BATCH AB1234")
        self.assertEqual(normalize_confusable_characters("62H127KI", "batch"), "62H127KI")

    def test_multi_variant_character_consensus_voting(self):
        """Positional character consensus voting across multiple OCR variants."""
        variants = [
            ("06/09/26", 0.90),
            ("06/09/2G", 0.82),
            ("06/09/26", 0.92),
            ("06/O9/26", 0.85),
        ]
        consensus_text, avg_conf, score = character_consensus_voting(variants, field_type="date")
        self.assertEqual(consensus_text, "06/09/26")
        self.assertGreaterEqual(score, 0.75)


class TestLayoutAssociation(unittest.TestCase):
    """Test two-column layout clustering, multi-word label grouping, and pair scoring."""

    def test_multi_word_label_grouping(self):
        """Tokens like 'USE' and 'BY' or 'NET' and 'WT' should be grouped into single label entities."""
        t1 = CanonicalToken("USE", "use", BoundingBox(50, 100, 90, 120), 0.9)
        t2 = CanonicalToken("BY", "by", BoundingBox(95, 100, 125, 120), 0.9)
        t3 = CanonicalToken("NET", "net", BoundingBox(50, 140, 90, 160), 0.9)
        t4 = CanonicalToken("WT", "wt", BoundingBox(95, 140, 125, 160), 0.9)
        t5 = CanonicalToken("500 g", "500 g", BoundingBox(300, 140, 360, 160), 0.9)

        labels, remaining = group_multi_word_labels([t1, t2, t3, t4, t5])
        label_texts = [l.text for l in labels]
        self.assertIn("USE BY", label_texts)
        self.assertIn("NET WT", label_texts)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].text, "500 g")

    def test_semantic_safety_rejects_cross_field_mismatches(self):
        """Semantic scoring must heavily penalize mismatched field types."""
        lbl_mfg = LabelEntity("manufacturing_date", "MFG", [], BoundingBox(50, 100, 100, 120), 0.9)
        val_price = ValueEntity("₹699", CanonicalToken("₹699", "₹699", BoundingBox(300, 100, 360, 120), 0.9), BoundingBox(300, 100, 360, 120), 0.9, {"mrp": 0.9})
        val_date = ValueEntity("06/09/26", CanonicalToken("06/09/26", "06/09/26", BoundingBox(300, 100, 380, 120), 0.9), BoundingBox(300, 100, 380, 120), 0.9, {"date": 0.9})

        # MFG + ₹699 should receive negative score
        score_mismatch, reasons_mismatch = score_label_value_pair(lbl_mfg, val_price, median_h=20.0, is_in_same_row=True)
        self.assertLess(score_mismatch, 40.0)
        self.assertTrue(any("mismatch" in r for r in reasons_mismatch))

        # MFG + 06/09/26 should receive very high positive score
        score_match, reasons_match = score_label_value_pair(lbl_mfg, val_date, median_h=20.0, is_in_same_row=True)
        self.assertGreater(score_match, 80.0)
        self.assertTrue(any("semantic_date_match" in r for r in reasons_match))

    def test_section_44_synthetic_perturbed_two_column_regression(self):
        """
        MOST IMPORTANT REGRESSION TEST (Section 44 of prompt):
        Labels:
          MFG (y=500)
          USE BY (y=540)
          BATCH (y=580)
          MRP (y=620)
        Values with deliberate vertical perturbation:
          06/09/26 (y=507)
          06/09/28 (y=553)
          AB1234 (y=574)
          ₹699 (y=628)
        The global assignment must correctly resolve:
          MFG -> 06/09/26
          USE BY -> 06/09/28
          BATCH -> AB1234
          MRP -> ₹699
        """
        # Labels column at x = 100
        t_mfg = CanonicalToken("MFG", "mfg", BoundingBox(100, 500, 160, 525), 0.95)
        t_use = CanonicalToken("USE", "use", BoundingBox(100, 540, 140, 565), 0.95)
        t_by = CanonicalToken("BY", "by", BoundingBox(145, 540, 175, 565), 0.95)
        t_batch = CanonicalToken("BATCH", "batch", BoundingBox(100, 580, 170, 605), 0.95)
        t_mrp = CanonicalToken("MRP", "mrp", BoundingBox(100, 620, 155, 645), 0.95)

        # Values column at x = 390-405, with perturbed y coordinates
        t_val_mfg = CanonicalToken("06/09/26", "06/09/26", BoundingBox(400, 507, 490, 532), 0.94)
        t_val_exp = CanonicalToken("06/09/28", "06/09/28", BoundingBox(390, 553, 480, 578), 0.94)
        t_val_batch = CanonicalToken("AB1234", "ab1234", BoundingBox(405, 574, 475, 599), 0.93)
        t_val_mrp = CanonicalToken("₹699", "₹699", BoundingBox(390, 628, 450, 653), 0.96)

        all_tokens = [t_mfg, t_use, t_by, t_batch, t_mrp, t_val_mfg, t_val_exp, t_val_batch, t_val_mrp]
        store = OCRTokenStore(word_tokens=all_tokens, image_shape=(1000, 1000))

        layout_struct, field_assignments = analyze_label_layout(store)

        self.assertTrue(layout_struct.is_structured)
        self.assertGreaterEqual(layout_struct.layout_confidence, 0.65)

        # Check exact field-to-value assignments
        self.assertIn("manufacturing_date", field_assignments)
        self.assertEqual(field_assignments["manufacturing_date"][1].text, "06/09/26")

        self.assertIn("expiry_date", field_assignments)
        self.assertEqual(field_assignments["expiry_date"][1].text, "06/09/28")

        self.assertIn("batch_number", field_assignments)
        self.assertEqual(field_assignments["batch_number"][1].text, "AB1234")

        self.assertIn("mrp", field_assignments)
        self.assertEqual(field_assignments["mrp"][1].text, "₹699")

        # Check layout confidence metric is present and high
        for f_name, assign in field_assignments.items():
            l_conf = assign[3]
            self.assertGreaterEqual(l_conf, 0.60)

    def test_split_token_merging(self):
        """Split tokens like '35' and 'g' or '₹' and '22.00' should merge into single value entities."""
        from src.extraction.layout_association import merge_split_value_tokens
        tok1 = CanonicalToken("35", "35", BoundingBox(400, 100, 420, 120), 0.95)
        tok2 = CanonicalToken("g", "g", BoundingBox(425, 100, 435, 120), 0.95)
        tok3 = CanonicalToken("₹", "₹", BoundingBox(400, 150, 410, 170), 0.95)
        tok4 = CanonicalToken("22.00", "22.00", BoundingBox(415, 150, 460, 170), 0.95)

        merged = merge_split_value_tokens([tok1, tok2, tok3, tok4], median_h=20.0)
        self.assertEqual(len(merged), 2)
        texts = [m.text for m in merged]
        self.assertIn("35 g", texts)
        self.assertIn("₹ 22.00", texts)

    def test_clipped_date_recognition(self):
        """Clipped edge date '15/04/202' should recover as '15/04/2027'."""
        from src.extraction import patterns
        ext = patterns.extract_date("EXP. DATE: 15/04/202")
        self.assertIsNotNone(ext)
        self.assertEqual(ext[0], "15/04/2027")

    def test_date_fallback_anti_collision(self):
        """When only one unanchored date is in image, it must not be assigned to both MFG and EXP."""
        from src.extraction.field_rankers import extract_dates_reliably
        single_date_tok = CanonicalToken("02/2011", "02/2011", BoundingBox(100, 100, 200, 125), 0.90, token_type="line")
        store = OCRTokenStore(line_tokens=[single_date_tok], word_tokens=[single_date_tok], image_shape=(1000, 1000))

        best_mfg, best_exp, notes = extract_dates_reliably(store)
        # One field can receive it, but both CANNOT have the exact same date!
        if best_mfg and best_exp:
            self.assertNotEqual(best_mfg.value, best_exp.value)


if __name__ == "__main__":
    unittest.main()
