"""
Unit Test Suite for Field Extraction, Semantic Negative Classification,
Date Chronology Integrity, and Decision Engine Arbitration.
"""
import unittest

import config
from src.utils.geometry import BoundingBox
from src.extraction.tokens import CanonicalToken, OCRTokenStore
from src.extraction.candidate import FieldCandidate
from src.extraction.decision_engine import arbitrate_candidates
from src.extraction.field_classifier import (
    looks_like_date,
    looks_like_phone,
    looks_like_fssai,
    looks_like_quantity,
    looks_like_unit_sale_price,
    looks_like_barcode,
    evaluate_bbox_quality,
)
from src.extraction.mrp_extractor import (
    find_mrp_anchors,
    extract_price_candidates_from_text,
    score_mrp_candidate,
)
from src.extraction.field_rankers import extract_dates_reliably


class TestSemanticClassifiers(unittest.TestCase):
    """Test that non-MRP text patterns are correctly flagged as negative semantics."""

    def test_looks_like_date(self):
        self.assertTrue(looks_like_date("06/2026")[0])
        self.assertTrue(looks_like_date("24/07/2026")[0])
        self.assertTrue(looks_like_date("2026-08-26")[0])
        self.assertTrue(looks_like_date("09/12/2025")[0])
        self.assertFalse(looks_like_date("360.00")[0])
        self.assertFalse(looks_like_date("120.00")[0])

    def test_looks_like_phone(self):
        self.assertTrue(looks_like_phone("1800-22-1234")[0])
        self.assertTrue(looks_like_phone("Tel: +91 9876543210")[0])
        self.assertTrue(looks_like_phone("Customer Care: 022-28371900")[0])
        self.assertFalse(looks_like_phone("MRP ₹430.00")[0])

    def test_looks_like_quantity(self):
        self.assertTrue(looks_like_quantity("Net Qty: 200 ml")[0])
        self.assertTrue(looks_like_quantity("500 g")[0])
        self.assertTrue(looks_like_quantity("1 kg")[0])
        self.assertFalse(looks_like_quantity("Rs. 699.00")[0])

    def test_looks_like_fssai(self):
        self.assertTrue(looks_like_fssai("Lic. No. 10013021000869")[0])
        self.assertTrue(looks_like_fssai("fssai 10020022011411")[0])
        self.assertFalse(looks_like_fssai("MRP 430.00")[0])

    def test_looks_like_barcode(self):
        self.assertTrue(looks_like_barcode("8901030865421")[0])
        self.assertFalse(looks_like_barcode("360.00")[0])

    def test_huge_bbox_penalty(self):
        # A 4-character number spanning 80% of image width should receive severe penalty
        huge_box = BoundingBox(10, 50, 850, 80)
        penalty, notes = evaluate_bbox_quality(huge_box, (1000, 1000), "6")
        self.assertLessEqual(penalty, -30.0)
        self.assertTrue(any("Excessive bbox width" in n or "Severe" in n for n in notes))

        # A compact box should receive no negative penalty (may receive positive bonus)
        compact_box = BoundingBox(100, 50, 200, 80)
        c_penalty, _ = evaluate_bbox_quality(compact_box, (1000, 1000), "360.00")
        self.assertGreaterEqual(c_penalty, 0.0)


class TestMRPExtractor(unittest.TestCase):
    """Test dedicated MRP candidate generation and normalization."""

    def test_anchor_detection_excludes_nutrition(self):
        line1 = CanonicalToken("Calories: 250 kcal", "calories: 250 kcal", BoundingBox(10, 10, 100, 30), 0.9, "paddle", "gray", "line")
        line2 = CanonicalToken("MRP: Rs. 360.00", "mrp: rs. 360.00", BoundingBox(10, 50, 100, 70), 0.9, "paddle", "gray", "line")
        store = OCRTokenStore(line_tokens=[line1, line2])
        anchors = find_mrp_anchors(store)
        anchor_texts = [a[0].text for a in anchors]
        self.assertIn("MRP: Rs. 360.00", anchor_texts)
        self.assertNotIn("Calories: 250 kcal", anchor_texts)

    def test_comma_decimal_normalization(self):
        bbox = BoundingBox(10, 10, 100, 30)
        cands = extract_price_candidates_from_text("Mrr, OF 120,00", bbox, "same_line", "MRP", bbox)
        values = [c.value for c in cands]
        self.assertIn("120.00", values)

    def test_ocr_letter_o_normalization(self):
        bbox = BoundingBox(10, 10, 100, 30)
        cands = extract_price_candidates_from_text("MRP 22 OO taxes", bbox, "same_line", "MRP", bbox)
        values = [c.value for c in cands]
        self.assertIn("22.00", values)

    def test_price_scoring_penalizes_calendar_year(self):
        cand_year = FieldCandidate("mrp", "2026", "EXP 2026", "EXP", BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10))
        cand_price = FieldCandidate("mrp", "360.00", "MRP 360.00", "MRP", BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10))
        store = OCRTokenStore()
        score_year = score_mrp_candidate(cand_year, (1000, 1000), store)
        score_price = score_mrp_candidate(cand_price, (1000, 1000), store)
        self.assertGreater(score_price, score_year + 30.0)


class TestDateChronologyIntegrity(unittest.TestCase):
    """Test strict Legal Metrology date validation and zero silent date swapping."""

    def test_valid_chronology_preserved(self):
        t_mfg = CanonicalToken("MFG DATE: 06/2026", "mfg date: 06/2026", BoundingBox(10, 10, 200, 30), 0.9, "paddle", "orig", "line")
        t_exp = CanonicalToken("EXP DATE: 05/2029", "exp date: 05/2029", BoundingBox(10, 40, 200, 60), 0.9, "paddle", "orig", "line")
        store = OCRTokenStore(line_tokens=[t_mfg, t_exp])
        best_mfg, best_exp, notes = extract_dates_reliably(store)
        self.assertIsNotNone(best_mfg)
        self.assertIsNotNone(best_exp)
        self.assertEqual(best_mfg.value, "06/2026")
        self.assertEqual(best_exp.value, "05/2029")
        self.assertTrue(any("Date chronology verified" in n for n in notes))

    def test_inverted_chronology_never_silently_swapped(self):
        # When MFG is parsed as 2029 and EXP as 2026, the system must NOT silently swap them.
        t_mfg = CanonicalToken("MFG: 05/2029", "mfg: 05/2029", BoundingBox(10, 10, 200, 30), 0.9, "paddle", "orig", "line")
        t_exp = CanonicalToken("EXP: 06/2026", "exp: 06/2026", BoundingBox(10, 40, 200, 60), 0.9, "paddle", "orig", "line")
        store = OCRTokenStore(line_tokens=[t_mfg, t_exp])
        best_mfg, best_exp, notes = extract_dates_reliably(store)
        # Verify manufacturing_date retained its assigned label (05/2029) and was NOT silently swapped with 06/2026
        self.assertEqual(best_mfg.value, "05/2029")
        self.assertEqual(best_exp.value, "06/2026")
        # Verify the conflict was flagged explicitly in validation notes and status set to needs_recheck
        self.assertEqual(best_mfg.status, "needs_recheck")
        self.assertEqual(best_exp.status, "needs_recheck")
        self.assertTrue(any("CRITICAL DATE CONFLICT" in n or "Chronology inversion" in n for n in notes))


class TestDecisionEngine(unittest.TestCase):
    """Test candidate arbitration and status assignment."""

    def test_verified_assignment_on_high_score(self):
        cand = FieldCandidate("mrp", "360.00", "MRP 360.00", "MRP", BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10), ocr_confidence=0.85)
        cand.field_score = 85.0
        best, summary = arbitrate_candidates("mrp", [cand])
        self.assertIsNotNone(best)
        self.assertEqual(best.status, "verified")
        self.assertGreaterEqual(best.final_confidence, 0.80)

    def test_ambiguity_detection(self):
        cand1 = FieldCandidate("mrp", "22", "MRP: Rs. 22", "MRP", BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10))
        cand1.field_score = 65.0
        cand2 = FieldCandidate("mrp", "35", "35", None, BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10))
        cand2.field_score = 63.0  # diff = 2.0 < margin 10.0
        best, summary = arbitrate_candidates("mrp", [cand1, cand2])
        self.assertIsNotNone(best)
        self.assertEqual(best.status, "needs_recheck")
        self.assertTrue(any("Ambiguity detected" in r for r in best.decision_reasons))

    def test_rejection_below_threshold(self):
        cand = FieldCandidate("mrp", "0", "0", None, BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10))
        cand.field_score = 25.0  # below DECISION_THRESHOLD_RECHECK (45.0)
        best, summary = arbitrate_candidates("mrp", [cand])
        self.assertIsNone(best)


if __name__ == "__main__":
    unittest.main()
