"""
Authoritative Standardized Structured Output Builder for Food/Product Label Compliance OCR.

This is the SINGLE authoritative output builder for the entire project.
It transforms raw OCR detections, Canonical Token Stores, layout analyses, field rankings,
and regulatory Rule 7 evaluations into the standardized audit-ready JSON schema.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import re
import numpy as np

import config
from src.utils.geometry import BoundingBox, calculate_iou
from src.compliance.rule_7 import (
    evaluate_rule_7_for_detection,
    summarize_rule_7_compliance,
    Rule7Evaluation,
    STATUS_UNABLE_TO_VERIFY,
)
from src.compliance.font_metrics import measure_font_metrics, FontMetrics
from src.output.schema import validate_or_raise, validate_output_schema


def classify_detection_type(text: str, bbox: Optional[BoundingBox] = None) -> str:
    """
    Deterministically classify an OCR detection into:
    'text', 'numeric', 'date', 'barcode', 'qr', 'mixed', 'unknown'
    """
    clean = text.strip()
    if not clean:
        return "unknown"

    # 1. Barcode check: 8-14 digits with narrow aspect ratio or barcode pattern
    digits_only = re.sub(r'\D', '', clean)
    if len(digits_only) in {8, 12, 13, 14} and len(clean) <= 16:
        if bbox and (bbox.width > 2.0 * bbox.height or bbox.height > 2.0 * bbox.width):
            return "barcode"
        if len(digits_only) == len(clean):
            return "barcode"

    # 2. Date check
    if re.search(r'\b(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2}[.\s-](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[.\s-]\d{2,4})\b', clean, re.IGNORECASE):
        return "date"

    # 3. Numeric check (pure numbers or decimal price)
    if re.match(r'^(?:[₹Rs.]\s*)?\d+(?:\.\d+)?(?:/-)?$', clean, re.IGNORECASE):
        return "numeric"

    # 4. Mixed check (number + unit e.g. 400g, 0.55/g, 100 ml, 1 N)
    if re.search(r'\d+(?:\.\d+)?\s*(?:g|gm|gms|kg|ml|l|ltr|pcs|tablets?|units?|/\w+|per\s*\w+)\b', clean, re.IGNORECASE):
        return "mixed"

    # 5. Text check: primarily alphabet characters
    alpha_count = sum(1 for c in clean if c.isalpha())
    if alpha_count >= 2:
        return "text"

    if any(c.isalnum() for c in clean):
        return "mixed"

    return "unknown"


def find_matching_detection_id(
    target_bbox: Optional[Dict[str, Any]],
    target_text: Optional[str],
    detections: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Find the source detection ID that produced a given extracted field
    using bounding box overlap (IoU/containment) or text matching.
    """
    if not detections:
        return None

    # 1. First priority: Bounding Box overlap
    if target_bbox:
        tb = BoundingBox(
            x_min=float(target_bbox.get("x_min", target_bbox.get("x", 0))),
            y_min=float(target_bbox.get("y_min", target_bbox.get("y", 0))),
            x_max=float(target_bbox.get("x_max", target_bbox.get("x", 0) + target_bbox.get("width", 0))),
            y_max=float(target_bbox.get("y_max", target_bbox.get("y", 0) + target_bbox.get("height", 0))),
        )

        best_iou = 0.0
        best_det_id = None
        for det in detections:
            db_dict = det["bounding_box"]
            db = BoundingBox(
                x_min=float(db_dict["x"]),
                y_min=float(db_dict["y"]),
                x_max=float(db_dict["x"] + db_dict["width"]),
                y_max=float(db_dict["y"] + db_dict["height"]),
            )
            iou = calculate_iou(tb, db)
            if iou > best_iou:
                best_iou = iou
                best_det_id = det["detection_id"]

            # Also check if target is inside detection box
            if (db.x_min - 10 <= tb.x_min and db.x_max + 10 >= tb.x_max and
                db.y_min - 10 <= tb.y_min and db.y_max + 10 >= tb.y_max):
                if best_iou < 0.3:
                    best_det_id = det["detection_id"]

        if best_det_id and best_iou > 0.05:
            return best_det_id

    # 2. Second priority: Text substring match
    if target_text:
        clean_target = str(target_text).strip().lower()
        if len(clean_target) >= 2:
            for det in detections:
                det_text = det["text"].strip().lower()
                if clean_target in det_text or det_text in clean_target:
                    return det["detection_id"]

    return None


def build_standardized_output(
    image_filename: str,
    image: Optional[np.ndarray],
    lines: List[Any],
    words: Optional[List[Any]] = None,
    field_result: Optional[Dict[str, Any]] = None,
    layout_struct: Optional[Any] = None,
    quality_report: Optional[Any] = None,
    orientation_meta: Optional[Dict[str, Any]] = None,
    calibration: Optional[Dict[str, Any]] = None,
    pdp: Optional[Dict[str, Any]] = None,
    package_id: Optional[str] = None,
    label_side: str = "back",
    blown_formed_moulded: bool = False,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Build the single authoritative standardized compliance JSON dictionary.
    Guarantees structural validity and complete audit traceability.
    """
    field_result = field_result or {}
    orientation_meta = orientation_meta or {}
    calibration = calibration or {}
    pdp = pdp_area_dict = pdp or {}

    # 1. Package ID & Processing Metadata
    stem = Path(image_filename).stem
    pkg_id = package_id or f"pkg_{stem}"
    img_id = f"img_{stem}"

    # Determine image dimensions
    if image is not None and hasattr(image, "shape"):
        img_h, img_w = int(image.shape[0]), int(image.shape[1])
    else:
        dims = getattr(quality_report, "dimensions", (1000, 1000))
        img_h, img_w = int(dims[0]), int(dims[1])

    # 2. Image Quality Report mapping
    if quality_report is not None:
        if hasattr(quality_report, "to_dict"):
            qr_dict = quality_report.to_dict()
        elif isinstance(quality_report, dict):
            qr_dict = quality_report
        else:
            qr_dict = {}
        raw_blur = float(qr_dict.get("blur_score", 50.0))
        blur_score = round(min(1.0, max(0.0, raw_blur / 1000.0)), 2)
        q_score = 0.95 if qr_dict.get("is_acceptable", True) else 0.40
        res_suff = img_w >= config.MIN_IMAGE_DIMENSION and img_h >= config.MIN_IMAGE_DIMENSION
    else:
        qr_dict = {}
        q_score = 0.90
        blur_score = 0.85
        res_suff = True

    orient_corrected = bool(orientation_meta.get("cardinal_rotation", 0) != 0)
    deskew_applied = bool(orientation_meta.get("fine_deskew_applied", False))

    # 3. Calibration details
    cal_ppm = calibration.get("pixels_per_mm")
    cal_avail = bool(cal_ppm is not None and float(cal_ppm) > 0)
    cal_source = str(calibration.get("source")) if cal_avail and calibration.get("source") else None
    cal_conf = float(calibration.get("confidence", 0.95)) if cal_avail else 0.0

    # 4. Principal Display Panel details
    pdp_area = pdp_area_dict.get("area_cm2")
    pdp_detected = bool(pdp_area is not None and float(pdp_area) > 0)
    pdp_w_px = float(pdp_area_dict["width_px"]) if pdp_detected and pdp_area_dict.get("width_px") else None
    pdp_h_px = float(pdp_area_dict["height_px"]) if pdp_detected and pdp_area_dict.get("height_px") else None
    pdp_w_cm = float(pdp_area_dict["width_cm"]) if pdp_detected and pdp_area_dict.get("width_cm") else None
    pdp_h_cm = float(pdp_area_dict["height_cm"]) if pdp_detected and pdp_area_dict.get("height_cm") else None
    pdp_area_val = float(pdp_area) if pdp_detected else None
    pdp_src = str(pdp_area_dict.get("measurement_source")) if pdp_detected and pdp_area_dict.get("measurement_source") else None
    pdp_conf = float(pdp_area_dict.get("confidence", 0.95)) if pdp_detected else 0.0

    image_obj = {
        "image_id": img_id,
        "filename": image_filename,
        "label_side": label_side,
        "width": img_w,
        "height": img_h,
        "image_quality": {
            "quality_score": q_score,
            "blur_score": blur_score,
            "resolution_sufficient": res_suff,
            "orientation_corrected": orient_corrected,
            "deskew_applied": deskew_applied,
        },
        "calibration": {
            "available": cal_avail,
            "pixels_per_mm": round(float(cal_ppm), 2) if cal_avail else None,
            "source": cal_source,
            "confidence": round(cal_conf, 2),
        },
        "principal_display_panel": {
            "detected": pdp_detected,
            "width_px": round(pdp_w_px, 1) if pdp_w_px is not None else None,
            "height_px": round(pdp_h_px, 1) if pdp_h_px is not None else None,
            "width_cm": round(pdp_w_cm, 2) if pdp_w_cm is not None else None,
            "height_cm": round(pdp_h_cm, 2) if pdp_h_cm is not None else None,
            "area_cm2": round(pdp_area_val, 2) if pdp_area_val is not None else None,
            "measurement_source": pdp_src,
            "confidence": round(pdp_conf, 2),
        },
    }

    # 5. Build Detections List
    # Use coherent OCR text lines as primary detections
    primary_boxes = lines if lines else (words or [])
    # Sort top to bottom, left to right
    sorted_boxes = sorted(primary_boxes, key=lambda b: (b.bbox.y_min, b.bbox.x_min))

    # Pre-extract layout mapping if layout_struct is available
    layout_pairs = []
    col_div_x = None
    if layout_struct is not None:
        if hasattr(layout_struct, "assigned_pairs"):
            layout_pairs = layout_struct.assigned_pairs
        elif isinstance(layout_struct, dict):
            layout_pairs = layout_struct.get("assigned_pairs", [])
        columns = getattr(layout_struct, "columns", None) or (layout_struct.get("columns") if isinstance(layout_struct, dict) else None)
        if columns and len(columns) >= 2:
            col_div_x = float(columns[0]["x_range"][1] + columns[1]["x_range"][0]) / 2.0

    field_details = field_result.get("field_details", {})
    extracted_fields_raw = field_result.get("fields", {})

    detections: List[Dict[str, Any]] = []
    rule_7_evaluations: List[Rule7Evaluation] = []

    for idx, box in enumerate(sorted_boxes):
        det_id = f"det_{idx + 1:03d}"
        raw_text = getattr(box, "text", "")
        norm_text = raw_text.strip()
        conf = float(getattr(box, "confidence", getattr(box, "ocr_confidence", 0.85)))

        # Bounding box
        b = box.bbox
        bbox_dict = {
            "x": int(b.x_min),
            "y": int(b.y_min),
            "width": int(b.width),
            "height": int(b.height),
        }

        # OCR Metadata
        engine = getattr(box, "engine", "ensemble")
        variant = getattr(box, "variant", "primary")
        preproc = getattr(box, "preprocessing", "original")
        source = getattr(box, "source", "ocr")

        ocr_meta = {
            "engine": str(engine),
            "pass": str(variant),
            "preprocessing": str(preproc),
            "source": str(source),
        }

        # Detection Type
        dtype = classify_detection_type(raw_text, b)

        # Layout mapping
        col_idx = None
        if col_div_x is not None:
            col_idx = 1 if b.center_x < col_div_x else 2

        role = "body"
        layout_conf = 0.0
        row_num = None

        # Check if in assigned pairs
        for p_idx, pair in enumerate(layout_pairs):
            l_box = pair.get("label_bbox", {})
            v_box = pair.get("value_bbox", {})
            if l_box and abs(l_box.get("y_min", 0) - b.y_min) < 15 and abs(l_box.get("x_min", 0) - b.x_min) < 20:
                role = "label"
                row_num = p_idx + 1
                layout_conf = float(pair.get("layout_confidence", 0.85))
                break
            elif v_box and abs(v_box.get("y_min", 0) - b.y_min) < 15 and abs(v_box.get("x_min", 0) - b.x_min) < 20:
                role = "value"
                row_num = p_idx + 1
                layout_conf = float(pair.get("layout_confidence", 0.85))
                break

        if role == "body" and b.y_min < img_h * 0.20 and b.height > 25:
            role = "heading"

        layout_dict = {
            "column": col_idx,
            "row": row_num,
            "role": role,
            "layout_confidence": round(layout_conf, 2),
        }

        # Field mapping for this detection
        pred_field = None
        cand_flag = False
        field_conf = 0.0

        for f_name, f_info in field_details.items():
            if not isinstance(f_info, dict):
                continue
            f_bbox = f_info.get("bbox") or f_info.get("value_bbox")
            if f_bbox:
                fb = BoundingBox(
                    x_min=float(f_bbox.get("x_min", f_bbox.get("x", 0))),
                    y_min=float(f_bbox.get("y_min", f_bbox.get("y", 0))),
                    x_max=float(f_bbox.get("x_max", f_bbox.get("x", 0) + f_bbox.get("width", 0))),
                    y_max=float(f_bbox.get("y_max", f_bbox.get("y", 0) + f_bbox.get("height", 0))),
                )
                if calculate_iou(b, fb) > 0.20 or (fb.x_min >= b.x_min - 5 and fb.x_max <= b.x_max + 5 and fb.y_min >= b.y_min - 5 and fb.y_max <= b.y_max + 5):
                    pred_field = f_name
                    cand_flag = True
                    field_conf = float(f_info.get("final_confidence", f_info.get("field_confidence", 0.85)))
                    break

        field_dict = {
            "predicted": pred_field,
            "candidate": cand_flag,
            "field_confidence": round(field_conf, 2),
        }

        # Font metrics measurement
        font_m = measure_font_metrics(image, b, raw_text)

        # Physical metrics
        if cal_avail and font_m.measurement_available and font_m.character_height_px is not None:
            char_h_mm = font_m.character_height_px / float(cal_ppm)
            min_w_mm = (font_m.minimum_character_width_px / float(cal_ppm)) if font_m.minimum_character_width_px is not None else None
            phys_dict = {
                "measurement_available": True,
                "character_height_mm": round(char_h_mm, 2),
                "minimum_character_width_mm": round(min_w_mm, 2) if min_w_mm is not None else None,
            }
        else:
            phys_dict = {
                "measurement_available": False,
                "character_height_mm": None,
                "minimum_character_width_mm": None,
            }

        # Rule 7 evaluation
        r7_eval = evaluate_rule_7_for_detection(
            text=raw_text,
            character_height_px=font_m.character_height_px,
            minimum_character_width_px=float(font_m.minimum_character_width_px) if font_m.minimum_character_width_px is not None else None,
            width_height_ratio=font_m.width_height_ratio,
            measurement_available=font_m.measurement_available,
            pixels_per_mm=float(cal_ppm) if cal_avail else None,
            pdp_area_cm2=float(pdp_area) if pdp_detected else None,
            blown_formed_moulded=blown_formed_moulded,
            detection_type=dtype,
        )
        rule_7_evaluations.append(r7_eval)

        det_dict = {
            "detection_id": det_id,
            "source_image_id": img_id,
            "text": raw_text,
            "normalized_text": norm_text,
            "confidence": round(conf, 2),
            "ocr_metadata": ocr_meta,
            "detection_type": dtype,
            "bounding_box": bbox_dict,
            "layout": layout_dict,
            "field": field_dict,
            "font_metrics": font_m.to_dict(),
            "physical_metrics": phys_dict,
            "rule_7": r7_eval.to_dict(),
        }
        detections.append(det_dict)

    # 6. Format Extracted Fields with complete source traceability
    # Map to standardized field names:
    # product_name, manufacturer, manufacturer_address, net_quantity, mrp, unit_sale_price,
    # packed_on, use_by_date, batch_lot_number, fssai_license, country_of_origin
    extracted_fields_std: Dict[str, Any] = {
        "product_name": None,
        "manufacturer": None,
        "manufacturer_address": None,
        "net_quantity": None,
        "mrp": None,
        "unit_sale_price": None,
        "packed_on": None,
        "use_by_date": None,
        "batch_lot_number": None,
        "fssai_license": None,
        "country_of_origin": None,
    }

    field_confs = field_result.get("confidence", {})

    # Helper to build field entry with traceability
    def build_field_entry(f_key: str, val: Any, extra_attrs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if val is None or val == "":
            return None
        f_info = field_details.get(f_key, {})
        target_bbox = f_info.get("bbox") or f_info.get("value_bbox")
        src_id = find_matching_detection_id(target_bbox, str(val), detections)
        conf_val = round(float(field_confs.get(f_key, 0.85)), 2)
        entry = {
            "value": str(val),
            "source_detection_id": src_id,
            "confidence": conf_val,
        }
        if extra_attrs:
            entry.update(extra_attrs)
        return entry

    # Product Name
    p_val = extracted_fields_raw.get("product_name")
    extracted_fields_std["product_name"] = build_field_entry("product_name", p_val)

    # Manufacturer
    m_val = extracted_fields_raw.get("manufacturer")
    extracted_fields_std["manufacturer"] = build_field_entry("manufacturer", m_val)

    # Manufacturer Address
    a_val = extracted_fields_raw.get("manufacturer_address")
    extracted_fields_std["manufacturer_address"] = build_field_entry("manufacturer_address", a_val)

    # Net Quantity (split numeric value and unit)
    q_val = extracted_fields_raw.get("net_quantity")
    if q_val:
        q_clean = str(q_val).strip()
        q_match = re.match(r'^(?:.*?(\d+(?:\.\d+)?))\s*([a-zA-Z]+.*)$', q_clean)
        num_val = q_match.group(1) if q_match else q_clean
        unit_val = q_match.group(2).strip() if q_match else None
        extracted_fields_std["net_quantity"] = build_field_entry("net_quantity", num_val, {"unit": unit_val})

    # MRP (currency INR)
    mrp_val = extracted_fields_raw.get("mrp")
    if mrp_val:
        extracted_fields_std["mrp"] = build_field_entry("mrp", mrp_val, {"currency": "INR"})

    # Unit Sale Price
    usp_val = extracted_fields_raw.get("unit_sale_price")
    if usp_val:
        usp_clean = str(usp_val).strip()
        u_match = re.match(r'^(?:.*?)(\d+(?:\.\d+)?)\s*(?:/|per)?\s*([a-zA-Z]+)$', usp_clean)
        usp_num = u_match.group(1) if u_match else usp_clean
        usp_unit = f"per_{u_match.group(2).lower()}" if u_match else None
        extracted_fields_std["unit_sale_price"] = build_field_entry("unit_sale_price", usp_num, {"unit": usp_unit})

    # Packed On (from manufacturing_date)
    mfg_val = extracted_fields_raw.get("manufacturing_date")
    extracted_fields_std["packed_on"] = build_field_entry("manufacturing_date", mfg_val)

    # Use By Date (from expiry_date)
    exp_val = extracted_fields_raw.get("expiry_date")
    extracted_fields_std["use_by_date"] = build_field_entry("expiry_date", exp_val)

    # Batch/Lot Number
    b_val = extracted_fields_raw.get("batch_number")
    extracted_fields_std["batch_lot_number"] = build_field_entry("batch_number", b_val)

    # FSSAI License
    lic_val = extracted_fields_raw.get("license_number")
    if lic_val:
        lic_entry = build_field_entry("license_number", lic_val)
        if lic_entry:
            extracted_fields_std["fssai_license"] = [lic_entry]
    else:
        extracted_fields_std["fssai_license"] = None

    # Country of Origin
    co_val = extracted_fields_raw.get("country_of_origin")
    extracted_fields_std["country_of_origin"] = build_field_entry("country_of_origin", co_val)

    # 7. Compliance Summary
    r7_summary = summarize_rule_7_compliance(rule_7_evaluations)
    compliance_summary = {
        "verified": r7_summary["verified"],
        "compliant": r7_summary["compliant"],
        "non_compliant": r7_summary["non_compliant"],
        "unable_to_verify": r7_summary["unable_to_verify"],
        "rule_7": r7_summary,
    }

    # 8. Assemble Final Structured Result Object
    output_result = {
        "package_id": pkg_id,
        "processing": {
            "pipeline_version": "3.0",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "ocr_status": field_result.get("ocr_status", "success"),
        },
        "images": [image_obj],
        "detections": detections,
        "extracted_fields": extracted_fields_std,
        "compliance_summary": compliance_summary,
        # Legacy compatibility keys for backwards-compatible consumers and benchmarks
        "image": image_filename,
        "ocr_status": field_result.get("ocr_status", "success"),
        "fields": extracted_fields_raw,
        "confidence": field_confs,
        "uncertain_fields": field_result.get("uncertain_fields", []),
        "validation_notes": field_result.get("validation_notes", []),
        "quality_report": qr_dict,
        "orientation": orientation_meta,
    }

    # 9. Schema Validation
    if validate:
        validate_or_raise(output_result)


    return output_result
