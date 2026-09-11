# ============================================================
# CORE ENGINE — OCR + AI + RULE VALIDATION
#
# Stage 4: Gemini Semantic Extraction (AI)
# Stage 5: Deterministic Legal Rule Validation (Pure Python)
#
# THE CONTRACT:
#   Input:  list of local image file paths (1-6 images)
#   Output: dict matching the ScanResponse schema
# ============================================================

import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Ensure backend root is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Stage 4 & 5 imports
try:
    from backend.extractors.gemini_extractor import GeminiSemanticExtractor
    from backend.legal_engine.engine import MetroScanLegalEngine
except ImportError:
    from extractors.gemini_extractor import GeminiSemanticExtractor
    from legal_engine.engine import MetroScanLegalEngine

from app.config import settings


# ── Rule ID mapping: Stage 5 rule IDs → ScanResponse rule codes ──
RULE_ID_TO_CODE = {
    "6(1)(a)": ("RULE_6_1_A_MFG", "Manufacturer / Packer Details", "Rule 6(1)(a)"),
    "6(1)(b)": ("RULE_6_1_B_NAME", "Generic / Common Commodity Name", "Rule 6(1)(b)"),
    "6(1)(c)": ("RULE_6_1_C_NET_QTY", "Net Quantity", "Rule 6(1)(c)"),
    "6(1)(d)": ("RULE_6_1_D_MFG_DATE", "Manufacturing / Packing Date", "Rule 6(1)(d)"),
    "6(1)(e)": ("RULE_6_1_E_MRP", "Maximum Retail Price (MRP)", "Rule 6(1)(e)"),
    "6(1)(f)": ("RULE_6_1_F_EXPIRY", "Best Before / Expiry Date", "Rule 6(1)(f)"),
    "6(1)(g)": ("RULE_6_1_G_CONSUMER", "Consumer Care Details", "Rule 6(1)(g)"),
    "6(1)(h)": ("RULE_6_1_H_ORIGIN", "Country of Origin", "Rule 6(1)(h)"),
    "6(1)(i)": ("RULE_6_1_I_USP", "Unit Sale Price (USP)", "Rule 6(1)(i)"),
    "6(3)":    ("RULE_6_3_FONT", "Minimum Font / Numeral Height", "Rule 6(3)"),
}

# Stage 5 status → ScanResponse status mapping
STATUS_MAP = {
    "PASS": "PASS",
    "FAIL": "FAIL",
    "UNCERTAIN": "WARNING",
    "NOT_APPLICABLE": "PASS",
}


def _run_ocr_on_images(image_paths: List[str], panel_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Runs PaddleOCR (via OCRBridge) on the provided images and returns an OCR payload
    compatible with the Stage 4 extractor input format.
    Falls back gracefully to secondary OCR or structured defaults if uninstalled.
    """
    try:
        from app.services.ocr_bridge import OCRBridge
        _gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        ocr_payload = OCRBridge.run_ocr(image_paths, gemini_api_key=_gemini_key, label_sides=panel_types)
        if ocr_payload and ocr_payload.get("detections"):
            logger.info(
                f"OCRBridge: Extracted {len(ocr_payload['detections'])} detections across "
                f"{len(image_paths)} image(s)."
            )
            return ocr_payload
        elif ocr_payload and ocr_payload.get("images"):
            # Valid image processed but 0 text detections found
            return ocr_payload
    except Exception as e:
        logger.warning(f"PaddleOCR bridge failed or not available ({e}), attempting fallback.")

    # Fallback to EasyOCR if installed
    try:
        import easyocr
        from PIL import Image
        import numpy as np
        reader = easyocr.Reader(['en'], gpu=False)
        package_id = f"pkg_{uuid.uuid4().hex[:12]}"
        images_meta = []
        detections = []
        reference_objects = []
        det_counter = 0

        for idx, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                logger.warning(f"Image file not found: {img_path}")
                continue

            try:
                with Image.open(img_path) as pil_img:
                    img_width, img_height = pil_img.size
            except Exception as e:
                img_width, img_height = 1920, 1080

            image_id = f"img_{idx:03d}"
            label_sides = ["front", "back", "side", "top", "bottom", "unspecified"]
            label_side = label_sides[idx] if idx < len(label_sides) else "unspecified"

            images_meta.append({
                "image_id": image_id,
                "label_side": label_side,
                "width": img_width,
                "height": img_height,
            })

            try:
                results = reader.readtext(img_path)
            except Exception as e:
                logger.warning(f"EasyOCR failed on {img_path}: {e}")
                continue

            for bbox_coords, text, confidence in results:
                det_counter += 1
                xs = [pt[0] for pt in bbox_coords]
                ys = [pt[1] for pt in bbox_coords]
                x_min = int(min(xs))
                y_min = int(min(ys))
                x_max = int(max(xs))
                y_max = int(max(ys))

                detections.append({
                    "detection_id": f"det_{det_counter:04d}",
                    "source_image_id": image_id,
                    "text": text,
                    "confidence": round(float(confidence), 4),
                    "bounding_box": {
                        "x": x_min,
                        "y": y_min,
                        "width": x_max - x_min,
                        "height": y_max - y_min,
                    },
                })

        return {
            "package_id": package_id,
            "images": images_meta,
            "reference_objects": reference_objects,
            "detections": detections,
        }
    except Exception as fallback_err:
        logger.warning(f"Fallback OCR also unavailable ({fallback_err}). Returning empty detections.")
        return {
            "package_id": f"pkg_{uuid.uuid4().hex[:12]}",
            "images": [],
            "reference_objects": [],
            "detections": [],
        }


def _map_compliance_to_declarations(
    compliance_result,
    raw_text: str = "",
) -> List[Dict[str, Any]]:
    """
    Maps Stage 5 ComplianceResult.rule_evaluations into the
    DeclarationResult dict format expected by the ScanResponse schema.
    """
    declarations = []

    for rule_eval in compliance_result.rule_evaluations:
        rule_id = rule_eval.rule_id
        mapping = RULE_ID_TO_CODE.get(rule_id)

        if mapping:
            rule_code, rule_name, citation = mapping
        else:
            # Fallback for unknown rule IDs
            rule_code = f"RULE_{rule_id.replace('(', '_').replace(')', '_').upper()}"
            rule_name = rule_eval.rule_name
            citation = f"Rule {rule_id}"

        # Map status
        status = STATUS_MAP.get(rule_eval.status, "WARNING")
        is_present = rule_eval.status not in ("FAIL",) or rule_eval.extracted_value is not None

        # Extract font height from evidence/details if available
        measured_font_height_mm = rule_eval.details.get("measured_height_mm")

        # Determine violation reason
        violation_reason = None
        if rule_eval.status == "FAIL":
            violation_reason = rule_eval.reason
        elif rule_eval.status == "UNCERTAIN":
            violation_reason = rule_eval.reason

        declarations.append({
            "rule_code": rule_code,
            "rule_name": rule_name,
            "extracted_value": rule_eval.extracted_value,
            "is_present": is_present,
            "status": status,
            "statutory_citation": citation,
            "measured_font_height_mm": measured_font_height_mm,
            "confidence_score": rule_eval.confidence,
            "violation_reason": violation_reason,
        })

    return declarations


def analyze_package(image_paths: list[str], panel_types: Optional[list[str]] = None) -> dict:
    """
    Run the full compliance pipeline on package images.

    Args:
        image_paths: List of local file paths to captured package images.
        panel_types: Optional list of panel side identifiers (e.g. ['front', 'back', 'mrp_panel', ...])

    Returns:
        dict with keys: product_name, brand_name, overall_status,
        compliance_score, raw_extracted_text, declarations,
        annotated_image_bytes
    """

    # ── Step 1: Run OCR on all images ──
    logger.info(f"Stage 1-3: Running OCR Engine on {len(image_paths)} images...")
    ocr_data = _run_ocr_on_images(image_paths, panel_types=panel_types)

    # Collect all raw text for reference
    raw_text = " ".join(det["text"] for det in ocr_data.get("detections", []))

    if not ocr_data["detections"]:
        logger.warning(
            "No text detected in any image (OCR returned 0 detections). "
            "Continuing pipeline — Gemini will evaluate images directly via Vision API."
        )
        # Do NOT abort — pass empty detections to Gemini. The extractor has a fallback.

    # ── Step 2: Stage 4 — Gemini Semantic Extraction ──
    logger.info("Stage 4: Running Gemini Semantic Extraction...")
    gemini_key = settings.GEMINI_API_KEY
    if not gemini_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured in .env. "
            "Stage 4 semantic extraction requires a valid Gemini API key."
        )

    extractor = GeminiSemanticExtractor(api_key=gemini_key)
    semantic_result = extractor.extract(ocr_data)

    # ── Step 3: Stage 5 — Deterministic Legal Rule Validation ──
    logger.info("Stage 5: Running Deterministic Legal Rule Validation (10 rules)...")
    engine = MetroScanLegalEngine()
    compliance_result = engine.evaluate(
        semantic_data=semantic_result,
        ocr_data=ocr_data,
    )

    # ── Step 4: Map to ScanResponse format ──
    declarations = _map_compliance_to_declarations(compliance_result, raw_text)

    # Determine overall status for ScanResponse
    overall_status_map = {
        "PASS": "COMPLIANT",
        "FAIL": "NON_COMPLIANT",
        "UNCERTAIN": "WARNING",
    }
    overall_status = overall_status_map.get(
        compliance_result.overall_status, "WARNING"
    )

    # Extract product and brand name from semantic result if available
    product_name = "Packaged Commodity"
    brand_name = "Unknown Brand"

    if isinstance(semantic_result, dict):
        # Gemini returns fields under "fields" key per the prompt schema
        fields = semantic_result.get("fields", {})
        if not isinstance(fields, dict):
            fields = {}

        # Try to get generic commodity name (field key: generic_common_name)
        gcn = (
            fields.get("generic_common_name")
            or fields.get("generic_commodity_name")  # backward compat
            or semantic_result.get("generic_common_name")
            or semantic_result.get("generic_commodity_name")
        )
        if gcn and str(gcn).strip():
            product_name = str(gcn).strip()

        # Try to get manufacturer/brand from manufacturer_packer_importer
        mfg = (
            fields.get("manufacturer_packer_importer")
            or semantic_result.get("manufacturer_packer_importer")
        )
        if mfg and str(mfg).strip():
            # The first comma-separated segment is typically the company name
            mfg_str = str(mfg).strip()
            # Extract company name: text before first comma or newline
            import re as _re
            company_match = _re.split(r"[,\n]", mfg_str)
            brand_name = company_match[0].strip() if company_match else mfg_str
            # Remove common prefixes like "Mfd. & Mkt. by:" etc.
            brand_name = _re.sub(
                r"^(?:mfd\.?\s*&?\s*mkt\.?\s*by\s*:|manufactured\s*(?:and|&)?\s*marketed\s*by\s*:|packed\s*by\s*:|manufactured\s*by\s*:)",
                "",
                brand_name,
                flags=_re.IGNORECASE,
            ).strip()

    logger.info(
        f"Pipeline complete: {product_name} | "
        f"Status: {overall_status} | "
        f"Score: {compliance_result.overall_score}/100"
    )

    return {
        "product_name": product_name,
        "brand_name": brand_name,
        "overall_status": overall_status,
        "compliance_score": compliance_result.overall_score,
        "raw_extracted_text": raw_text,
        "declarations": declarations,
        "annotated_image_bytes": None,  # Can be enhanced later with bounding box overlays
    }

