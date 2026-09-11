"""
Rule 6(3): Minimum Height of Numerals and Letters.
Statutory Reference: Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(3) & Table 1.
"""

from typing import Dict, Any, Optional
from backend.legal_engine.models import RuleEvaluation, EvidenceItem

# Standard EAN-13 Barcode Dimensions under GS1 specifications
STANDARD_EAN13_WIDTH_MM = 37.29
STANDARD_EAN13_HEIGHT_MM = 25.91

# Statutory minimum numeral heights under Rule 6(3) Table 1
def get_statutory_min_height_mm(pdp_area_sq_cm: Optional[float] = None) -> float:
    """
    Legal Metrology (Packaged Commodities) Rules, 2011, Table 1:
      <= 100 cm²        -> >= 1.0 mm
      100 to 500 cm²    -> >= 2.0 mm
      500 to 2500 cm²   -> >= 4.0 mm
      > 2500 cm²        -> >= 6.0 mm
    """
    if pdp_area_sq_cm is None:
        return 2.0  # Default standard retail package
    if pdp_area_sq_cm <= 100:
        return 1.0
    elif pdp_area_sq_cm <= 500:
        return 2.0
    elif pdp_area_sq_cm <= 2500:
        return 4.0
    else:
        return 6.0

DEFAULT_MIN_NUMERAL_HEIGHT_MM = 2.0


def evaluate_rule_6_3(semantic_data: Dict[str, Any], ocr_data: Dict[str, Any] = None) -> RuleEvaluation:
    rule_id = "6(3)"
    rule_name = "Minimum Height of Numerals and Letters"

    ocr_data = ocr_data or {}
    ref_objects = ocr_data.get("reference_objects", [])
    
    OPTICAL_TOLERANCE_MM = 0.10  # Standard optical quantization tolerance

    # 1. Check if physical measurement already pre-calculated in Stage 3
    stage3_font_info = semantic_data.get("font_measurement") or ocr_data.get("font_measurement")
    if stage3_font_info and stage3_font_info.get("measured_height_mm") is not None:
        measured_mm = float(stage3_font_info["measured_height_mm"])
        min_required = float(stage3_font_info.get("minimum_required_mm", DEFAULT_MIN_NUMERAL_HEIGHT_MM))
        
        if measured_mm >= (min_required - OPTICAL_TOLERANCE_MM):
            return RuleEvaluation(
                rule_id=rule_id,
                rule_name=rule_name,
                status="PASS",
                reason=f"Measured numeral height of {measured_mm:.2f} mm meets required minimum threshold ({min_required:.2f} mm).",
                extracted_value=f"{measured_mm:.2f} mm",
                evidence=[],
                confidence=0.9,
                details={"measured_height_mm": measured_mm, "min_required_mm": min_required}
            )
        else:
            return RuleEvaluation(
                rule_id=rule_id,
                rule_name=rule_name,
                status="FAIL",
                reason=f"Measured numeral height of {measured_mm:.2f} mm is below the statutory minimum of {min_required:.2f} mm.",
                extracted_value=f"{measured_mm:.2f} mm",
                evidence=[],
                confidence=0.9,
                details={"measured_height_mm": measured_mm, "min_required_mm": min_required}
            )

    # 2. Check for reference objects (e.g. EAN-13 barcode) in ocr_data
    barcode_ref = None
    for ref in ref_objects:
        if ref.get("type") in ["ean_13_barcode", "barcode", "upc_barcode"]:
            barcode_ref = ref
            break

    if not barcode_ref or not barcode_ref.get("bounding_box"):
        return RuleEvaluation(
            rule_id=rule_id,
            rule_name=rule_name,
            status="UNCERTAIN",
            reason="No physical reference object (e.g., standard EAN-13 barcode) detected in OCR to establish real-world pixel-to-millimeter scale. Physical inspection required.",
            extracted_value=None,
            evidence=[],
            confidence=0.5
        )

    # 3. Calculate pixels per mm from barcode
    bbox = barcode_ref["bounding_box"]
    barcode_w_px = barcode_ref.get("barcode_width_px") or bbox.get("width", 0)
    if barcode_w_px <= 0:
        barcode_w_px = max(bbox.get("width", 0), bbox.get("height", 0))

    if barcode_w_px <= 0:
        return RuleEvaluation(
            rule_id=rule_id,
            rule_name=rule_name,
            status="UNCERTAIN",
            reason="Barcode bounding box has invalid dimensions; cannot calibrate physical scale.",
            extracted_value=None,
            evidence=[],
            confidence=0.5
        )

    pixels_per_mm = barcode_w_px / STANDARD_EAN13_WIDTH_MM

    # Map detection_id to raw OCR detection for robust fallback lookup
    det_map = {}
    import re
    for d in ocr_data.get("detections", []):
        if isinstance(d, dict) and d.get("detection_id"):
            raw_id = str(d["detection_id"])
            det_map[raw_id] = d
            det_map[raw_id.lower()] = d
            m = re.search(r'\d+', raw_id)
            if m:
                det_map[m.group()] = d
                det_map[f"det_{int(m.group()):04d}"] = d
                det_map[f"det_{int(m.group())}"] = d

    evidence_meta = semantic_data.get("evidence", {})
    ref_image_id = barcode_ref.get("source_image_id")
    fields = semantic_data.get("fields", {}) if isinstance(semantic_data.get("fields"), dict) else {}

    # Collect candidate declaration numerals in order of legal priority
    candidates = []
    for field_key in ["net_quantity", "mrp", "manufacturing_packing_import_date"]:
        ev = evidence_meta.get(field_key)
        box = None
        src_img = None
        det_id = None
        raw_text = None

        if ev and isinstance(ev, dict):
            box = ev.get("bounding_box")
            src_img = ev.get("source_image_id")
            det_id = ev.get("detection_id")
            raw_text = ev.get("raw_source_text")

        # 1. Try matching by detection_id in det_map
        if not box and det_id and str(det_id) in det_map:
            matched = det_map[str(det_id)]
            box = matched.get("bounding_box")
            src_img = matched.get("source_image_id")
            raw_text = raw_text or matched.get("text")

        all_dets = ocr_data.get("detections", [])
        same_img_dets = [d for d in all_dets if d.get("source_image_id") == ref_image_id]
        search_dets = same_img_dets if same_img_dets else all_dets

        # 2. Try matching by raw text substring in raw OCR detections
        if not box and raw_text:
            raw_text_clean = str(raw_text).strip().lower()
            for d in search_dets:
                d_text = str(d.get("text", "")).strip().lower()
                if d_text and (raw_text_clean in d_text or d_text in raw_text_clean):
                    b = d.get("bounding_box")
                    if b and b.get("height", 0) > 0 and b.get("height", 0) < 300:
                        box = b
                        src_img = d.get("source_image_id")
                        det_id = det_id or d.get("detection_id")
                        break

        # 3. Try matching by semantic field value digits (e.g. net_quantity digits "225")
        if not box and fields.get(field_key):
            field_val = str(fields[field_key]).strip()
            digits = re.findall(r'\d+', field_val)
            if digits:
                target_num = digits[0]
                for d in search_dets:
                    d_text = str(d.get("text", ""))
                    if target_num in d_text:
                        b = d.get("bounding_box")
                        if b and b.get("height", 0) > 0 and b.get("height", 0) < 300:
                            box = b
                            src_img = d.get("source_image_id")
                            det_id = det_id or d.get("detection_id")
                            raw_text = raw_text or d_text
                            break

        if box and isinstance(box, dict) and box.get("height", 0) > 0:
            is_same_image = bool(ref_image_id and src_img == ref_image_id)
            candidates.append({
                "box": box,
                "text": raw_text,
                "det_id": det_id,
                "src_img": src_img,
                "is_same_image": is_same_image,
                "field_key": field_key,
            })

    # 4. If no candidates from semantic evidence, search raw detections directly on reference image
    if not candidates:
        all_dets = ocr_data.get("detections", [])
        same_dets = [d for d in all_dets if d.get("source_image_id") == ref_image_id]
        search_dets = same_dets if same_dets else all_dets

        patterns = [
            # Net quantity pattern e.g. 225g, 500 ml, 1 kg
            r'\b\d+(?:\.\d+)?\s*(?:g|gm|gms|kg|ml|l|ltr|litres?)\b',
            # MRP pattern e.g. ₹ 249, MRP 249.00, Rs 50
            r'(?:mrp|₹|rs\.?)\s*\d+',
            # Date pattern e.g. 02/06/2026, 06/26
            r'\b\d{2}[/\-.]\d{2}[/\-.]\d{2,4}\b',
            # General standalone numeral
            r'\b\d{2,4}\b',
        ]

        for pat in patterns:
            for d in search_dets:
                d_text = str(d.get("text", ""))
                if re.search(pat, d_text, re.IGNORECASE):
                    b = d.get("bounding_box")
                    if b and isinstance(b, dict) and b.get("height", 0) > 0:
                        candidates.append({
                            "box": b,
                            "text": d_text,
                            "det_id": d.get("detection_id"),
                            "src_img": d.get("source_image_id"),
                            "is_same_image": bool(ref_image_id and d.get("source_image_id") == ref_image_id),
                            "field_key": "ocr_numeral",
                        })
                        break
            if candidates:
                break

    # Prioritize declaration numerals located on the SAME image as the reference barcode
    target_candidate = None
    if candidates:
        same_img_candidates = [c for c in candidates if c["is_same_image"]]
        target_candidate = same_img_candidates[0] if same_img_candidates else candidates[0]

    if not target_candidate:
        return RuleEvaluation(
            rule_id=rule_id,
            rule_name=rule_name,
            status="UNCERTAIN",
            reason="Barcode detected but target numeral bounding box could not be isolated for height measurement.",
            extracted_value=None,
            evidence=[],
            confidence=0.5
        )

    target_box = target_candidate["box"]
    target_text = target_candidate["text"]
    target_det_id = target_candidate["det_id"]
    source_img = target_candidate["src_img"]

    # Calculate measured height in millimetres (per text line if multi-line block)
    raw_box_height = float(target_box.get("height", 0))
    lines = [line.strip() for line in str(target_text).replace('\\n', '\n').replace(r'\n', '\n').splitlines() if line.strip()]
    num_lines = max(1, len(lines))
    numeral_height_px = raw_box_height / num_lines
    measured_height_mm = numeral_height_px / pixels_per_mm
    pdp_area = semantic_data.get("pdp_area_sq_cm") or ocr_data.get("pdp_area_sq_cm")
    min_required_mm = get_statutory_min_height_mm(pdp_area)

    evidence_items = [
        EvidenceItem(
            detection_id=target_det_id,
            source_text=target_text,
            source_image_id=source_img,
            bounding_box=target_box,
            confidence=0.92
        )
    ]

    if measured_height_mm >= (min_required_mm - OPTICAL_TOLERANCE_MM):
        return RuleEvaluation(
            rule_id=rule_id,
            rule_name=rule_name,
            status="PASS",
            reason=f"Measured declaration numeral height of {measured_height_mm:.2f} mm satisfies minimum threshold ({min_required_mm:.2f} mm) calibrated via barcode.",
            extracted_value=f"{measured_height_mm:.2f} mm",
            evidence=evidence_items,
            confidence=0.92,
            details={
                "measured_height_mm": round(measured_height_mm, 2),
                "minimum_required_mm": min_required_mm,
                "pixels_per_mm": round(pixels_per_mm, 2),
                "calibration_reference": "EAN-13 Barcode (37.29 mm)"
            }
        )
    else:
        return RuleEvaluation(
            rule_id=rule_id,
            rule_name=rule_name,
            status="FAIL",
            reason=f"Measured declaration numeral height of {measured_height_mm:.2f} mm is below the statutory minimum ({min_required_mm:.2f} mm) calibrated via barcode.",
            extracted_value=f"{measured_height_mm:.2f} mm",
            evidence=evidence_items,
            confidence=0.92,
            details={
                "measured_height_mm": round(measured_height_mm, 2),
                "minimum_required_mm": min_required_mm,
                "pixels_per_mm": round(pixels_per_mm, 2),
                "calibration_reference": "EAN-13 Barcode (37.29 mm)"
            }
        )
