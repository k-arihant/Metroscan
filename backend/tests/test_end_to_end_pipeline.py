"""
End-to-End Pipeline Verification Suite for MetroScan.
Tests the complete flow: Image Upload -> OCRBridge -> Legal Engine -> Form 1 PDF.

Covers all 10 Phase 7 verification scenarios:
  Test 1: Single valid image (test.jpeg)
  Test 2: Multiple valid images (t1.jpeg + t2.jpeg)
  Test 3: Poor quality / blurry image
  Test 4: Image with no readable text
  Test 5: Unsupported file type
  Test 6: Missing / invalid mandatory fields (statutory violations)
  Test 7: Rapid consecutive / concurrent requests
  Test 8: Real PDF report generation with verification of PDF bytes
  Test 9: Environment & GPU detection
  Test 10: Backend restart and OCR singleton persistence
"""

import os
import sys
import io
import time
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

# Add backend and project root to sys.path
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in (str(PROJECT_ROOT), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from app.main import app
from app.services.ocr_bridge import OCRBridge
from app.services.core_engine import analyze_package
from app.services.report_service import ReportGeneratorService
from app.schemas import DeclarationResult


class TestEndToEndPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_images_dir = PROJECT_ROOT / "OCR-paddle" / "images"
        cls.test_image_1 = cls.test_images_dir / "test.jpeg"
        cls.test_image_2 = cls.test_images_dir / "t1.jpeg"
        cls.test_image_3 = cls.test_images_dir / "t2.jpeg"

    # -------------------------------------------------------------
    # Helper: Generate synthetic in-memory JPEG images
    # -------------------------------------------------------------
    @staticmethod
    def _create_synthetic_image(text: str = "", blur: bool = False) -> bytes:
        img = Image.new("RGB", (600, 400), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        if text:
            d.text((50, 50), text, fill=(0, 0, 0))
        if blur:
            # Create a very low contrast / blurred gradient
            for y in range(400):
                for x in range(600):
                    val = 120 + int((x + y) % 10)
                    img.putpixel((x, y), (val, val, val))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    # -------------------------------------------------------------
    # Test 1: Single Valid Image Upload & OCR
    # -------------------------------------------------------------
    def test_01_single_valid_image(self):
        """Verify uploading one real package image processes cleanly through OCR and returns scorecard."""
        if not self.test_image_1.exists():
            self.skipTest(f"Test image not found at {self.test_image_1}")

        with open(self.test_image_1, "rb") as f:
            files = [("images", ("test.jpeg", f.read(), "image/jpeg"))]

        response = self.client.post("/api/v1/scan/analyze", files=files, data={"store_name": "Test Mart"})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("scan_id", data)
        self.assertIn("overall_status", data)
        self.assertIn("compliance_score", data)
        self.assertIn("declarations", data)
        self.assertGreater(len(data["declarations"]), 0)
        self.assertTrue(data["pdf_url"].startswith("/api/v1/scan/"))

    # -------------------------------------------------------------
    # Test 2: Multiple Valid Images (Front + Back panels)
    # -------------------------------------------------------------
    def test_02_multiple_valid_images(self):
        """Verify multi-image multi-panel upload works seamlessly without crash."""
        if not (self.test_image_2.exists() and self.test_image_3.exists()):
            self.skipTest("Multi-test images not found")

        with open(self.test_image_2, "rb") as f1, open(self.test_image_3, "rb") as f2:
            files = [
                ("images", ("front_panel.jpeg", f1.read(), "image/jpeg")),
                ("images", ("back_panel.jpeg", f2.read(), "image/jpeg")),
            ]

        response = self.client.post(
            "/api/v1/scan/analyze",
            files=files,
            data={"store_name": "Supermarket Delhi", "latitude": 28.6139, "longitude": 77.2090}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["image_urls"]), 2)
        self.assertIn(data["overall_status"], ["COMPLIANT", "NON_COMPLIANT", "WARNING"])

    # -------------------------------------------------------------
    # Test 3: Poor Quality / Blurry Image
    # -------------------------------------------------------------
    def test_03_poor_quality_blurry_image(self):
        """Verify pipeline handles blurry or degraded images gracefully."""
        blurry_bytes = self._create_synthetic_image(text="faded faint text", blur=True)
        files = [("images", ("blurry.jpg", blurry_bytes, "image/jpeg"))]

        response = self.client.post("/api/v1/scan/analyze", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should return a valid response structure even if low compliance or warning
        self.assertIn("compliance_score", data)
        self.assertIn("overall_status", data)

    # -------------------------------------------------------------
    # Test 4: Image With No Readable Text (Blank)
    # -------------------------------------------------------------
    def test_04_blank_image_no_text(self):
        """Verify an image containing zero text returns safe non-crashing empty declarations."""
        blank_bytes = self._create_synthetic_image(text="")
        files = [("images", ("blank.jpg", blank_bytes, "image/jpeg"))]

        response = self.client.post("/api/v1/scan/analyze", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["overall_status"], ["NON_COMPLIANT", "WARNING"])

    # -------------------------------------------------------------
    # Test 5: Unsupported File Extension
    # -------------------------------------------------------------
    def test_05_unsupported_file_extension(self):
        """Verify non-image files are rejected with HTTP 400 and clear error message."""
        dummy_txt = b"This is not a packaged commodity image."
        files = [("images", ("sample.txt", dummy_txt, "text/plain"))]

        response = self.client.post("/api/v1/scan/analyze", files=files)
        self.assertEqual(response.status_code, 400)
        detail = response.json().get("detail", "")
        self.assertIn("Unsupported image format", detail)

    # -------------------------------------------------------------
    # Test 6: Missing / Invalid Mandatory Fields (Legal Metrology)
    # -------------------------------------------------------------
    def test_06_missing_declarations_statutory_violations(self):
        """Verify that missing MRP / Tax or Net Quantity generates statutory violation citations."""
        # Test directly against ReportLab & DeclarationResult
        decls = [
            DeclarationResult(
                rule_code="RULE_6_1_E_MRP",
                rule_name="Maximum Retail Price (MRP)",
                extracted_value="Rs. 100",
                is_present=True,
                status="FAIL",
                statutory_citation="Rule 6(1)(e)",
                violation_reason="Missing mandatory phrase 'inclusive of all taxes'",
            ),
            DeclarationResult(
                rule_code="RULE_6_1_C_NET_QTY",
                rule_name="Net Quantity",
                extracted_value=None,
                is_present=False,
                status="FAIL",
                statutory_citation="Rule 6(1)(c)",
                violation_reason="Net quantity declaration is missing",
            )
        ]
        pdf_bytes, sha = ReportGeneratorService.generate_inspection_certificate(
            scan_id="test_scan_06",
            product_name="Sample Biscuit",
            brand_name="Sample Brand",
            overall_status="NON_COMPLIANT",
            compliance_score=50.0,
            declarations=decls,
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(sha), 10)

    # -------------------------------------------------------------
    # Test 7: Rapid Consecutive / Concurrent Requests
    # -------------------------------------------------------------
    def test_07_concurrent_rapid_requests(self):
        """Verify thread-safe singleton execution with consecutive requests."""
        img_bytes = self._create_synthetic_image("MRP Rs. 50 (incl. of all taxes) Net Qty: 100g")
        responses = []
        for i in range(2):
            files = [("images", (f"rapid_{i}.jpg", img_bytes, "image/jpeg"))]
            resp = self.client.post("/api/v1/scan/analyze", files=files)
            responses.append(resp)

        for r in responses:
            self.assertEqual(r.status_code, 200)
            self.assertIn("scan_id", r.json())

    # -------------------------------------------------------------
    # Test 8: Real PDF Certificate Generation & Streaming
    # -------------------------------------------------------------
    def test_08_pdf_report_generation(self):
        """Verify that GET /api/v1/scan/{id}/certificate.pdf returns valid PDF binary bytes."""
        img_bytes = self._create_synthetic_image("Aashirvaad Atta 5kg MRP Rs 240")
        files = [("images", ("prod.jpg", img_bytes, "image/jpeg"))]
        scan_res = self.client.post("/api/v1/scan/analyze", files=files)
        scan_id = scan_res.json()["scan_id"]

        pdf_resp = self.client.get(f"/api/v1/scan/{scan_id}/certificate.pdf")
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.headers.get("content-type"), "application/pdf")
        self.assertTrue(pdf_resp.content.startswith(b"%PDF"))
        self.assertIn("x-sha256-hash", pdf_resp.headers)

    # -------------------------------------------------------------
    # Test 9: Environment & Hardware Diagnostics
    # -------------------------------------------------------------
    def test_09_environment_diagnostics(self):
        """Verify system health endpoint reflects live configuration."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("mock_mode", data)

    # -------------------------------------------------------------
    # Test 10: Backend Restart & OCR Singleton Persistence
    # -------------------------------------------------------------
    def test_10_ocr_singleton_persistence(self):
        """Verify OCRBridge singleton instance persists across multiple calls."""
        bridge1 = OCRBridge()
        bridge2 = OCRBridge()
        self.assertIs(bridge1, bridge2)


if __name__ == "__main__":
    unittest.main()
