"""
Field Extraction Coordinator.
Orchestrates Canonical Token Store construction, dedicated candidate generation,
negative classification, field-specific ranking, targeted patch re-OCR, and structured audit output.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

import config
from src.ocr.engine_manager import OCRBox
from src.extraction import patterns, validator
from src.extraction.tokens import CanonicalToken, OCRTokenStore
from src.extraction.candidate import FieldCandidate
from src.extraction.layout_association import analyze_label_layout
from src.ocr.dot_matrix import run_dot_matrix_ocr
from src.utils.layout_visualizer import draw_layout_debug_image
from src.extraction.mrp_extractor import extract_mrp_reliably
from src.extraction.field_rankers import (
    extract_dates_reliably,
    extract_quantity_reliably,
    extract_batch_reliably,
    extract_license_reliably,
    extract_usp_reliably,
)


def extract_product_name(lines: List[OCRBox]) -> Optional[Tuple[str, float]]:
    """
    Extract product name from candidate top-level or prominent lines.
    Prioritizes upper region of label above compliance details, scored by font height.
    """
    if not lines:
        return None

    exclude_regex = re.compile(
        r'\b(net|mrp|m\.r\.p|mfg|exp|batch|lot|fssai|lic|licence|date|quantity|weight|usp|price|ingredients|nutrition|table|contact|feedback|address|office|pvt|ltd|pack|packed|store|cool|dry|authentic|warning|direction|caution|details|email|website|phone|registered|for\s*sale|dist|village|mandal|nagar|pincode|pin-|survey\s*no|shed\s*no|road|bhawan|nagpur|gadchiroli|telangana|gujarat|surat)\b',
        re.IGNORECASE
    )

    # Find where compliance info starts
    compliance_y = 999999.0
    for line in lines:
        if re.search(r'\b(net\s*(?:quantity|wt|weight)|m\.?r\.?p|batch\s*no|lic\s*no)\b', line.text, re.IGNORECASE):
            compliance_y = min(compliance_y, line.bbox.y_min)

    # Evaluate lines positioned above or near the compliance panel
    candidates = []
    for line in lines:
        text = line.text.strip()
        text_clean = re.sub(r'[^A-Za-z0-9\s-]', '', text).strip()
        words = text_clean.split()
        if not words:
            continue

        letters = sum(1 for c in text_clean if c.isalpha())
        if letters < 3:
            continue

        if exclude_regex.search(text):
            continue

        # Check if line is above compliance panel
        is_above_compliance = line.bbox.y_min < compliance_y
        position_bonus = 1.5 if is_above_compliance else 0.8

        # Height represents font size
        font_height = line.bbox.height
        score = font_height * line.confidence * position_bonus

        candidates.append((score, text_clean, line.confidence, line.bbox))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_text = candidates[0][1]
        best_conf = candidates[0][2]
        best_bbox = candidates[0][3]
        return best_text, min(0.95, best_conf), best_bbox

    return None


def extract_manufacturer(lines: List[OCRBox]) -> Optional[Tuple[str, float, Any]]:
    """Extract manufacturer / packer company name."""
    mfg_regex = re.compile(
        r'(?:mfd\.?\s*by|mfg\.?\s*by|manufactured\s*by|marketed\s*by|packed\s*by)[\s.:]*(.+)',
        re.IGNORECASE
    )
    for line in lines:
        match = mfg_regex.search(line.text)
        if match:
            cand = match.group(1).strip()
            if len(cand) > 3:
                return cand, min(0.95, line.confidence), line.bbox

    # Look for corporate suffixes
    for line in lines:
        if re.search(r'\b(pvt\.?\s*ltd\.?|private\s*limited|limited|foods|bakery|laboratories|enterprises)\b', line.text, re.IGNORECASE):
            if not line.text.lower().startswith("regd") and not line.text.lower().startswith("dist"):
                return line.text.strip(), min(0.90, line.confidence), line.bbox

    return None


def extract_all_fields(
    lines: List[OCRBox],
    words: List[OCRBox],
    image_filename: str = "",
    image: Optional[np.ndarray] = None,
    engine_mgr: Any = None,
) -> Dict[str, Any]:
    """
    Extract all compliance label fields using evidence-driven candidate ranking,
    dedicated MRP pipeline, strict negative classification, and Decision Engine arbitration.
    Returns structured JSON-compatible dictionary.
    """
    extracted_fields: Dict[str, Any] = {}
    confidence_dict: Dict[str, float] = {}
    field_details: Dict[str, Any] = {}
    uncertain_fields: List[str] = []
    validation_notes: List[str] = []

    # -------------------------------------------------------------
    # 1. Construct Canonical OCR Token Store
    # -------------------------------------------------------------
    img_shape = image.shape[:2] if image is not None else (1000, 1000)
    token_store = OCRTokenStore.from_ocr_boxes(words, lines, image_shape=img_shape)

    # -------------------------------------------------------------
    # 1b. Layout-Aware Table Structure & Association (Stage 2)
    # -------------------------------------------------------------
    layout_struct = None
    layout_candidates: Dict[str, FieldCandidate] = {}
    if config.LAYOUT_DETECTION_ENABLED:
        layout_struct, field_assignments = analyze_label_layout(token_store)

        # Targeted value-column re-OCR: If a key label row is missing its value, crop value column and run dot-matrix OCR
        if layout_struct.is_structured and image is not None and engine_mgr is not None and len(layout_struct.columns) >= 2:
            val_col = layout_struct.columns[1]
            img_h, img_w = image.shape[:2]
            reocr_tokens_added = False

            for row in layout_struct.rows:
                if not row.label:
                    continue

                # Check if this row already has a semantically valid candidate
                has_valid_val = False
                if row.values:
                    for v in row.values:
                        if "date" in row.label.field_name and patterns.extract_date(v.text):
                            has_valid_val = True
                            break
                        elif row.label.field_name == "mrp" and patterns.extract_mrp(v.text):
                            has_valid_val = True
                            break
                        elif row.label.field_name == "net_quantity" and patterns.extract_net_quantity(v.text):
                            has_valid_val = True
                            break
                        elif row.label.field_name == "batch_number" and patterns.extract_batch_number(v.text):
                            has_valid_val = True
                            break

                if not has_valid_val:
                    # Missing or unverified value in this row -> targeted dot-matrix re-OCR
                    y1 = max(0, int(row.y_min - 10))
                    y2 = min(img_h, int(row.y_max + 12))
                    x1 = max(0, int(row.label.bbox.x_max + 5))
                    x2 = min(img_w, int(row.label.bbox.x_max + max(row.label.bbox.height * 14, 350)))

                    crop = image[y1:y2, x1:x2]
                    if crop.size > 0 and crop.shape[0] >= 10 and crop.shape[1] >= 10:
                        exp_field = "date" if "date" in row.label.field_name else ("mrp" if row.label.field_name == "mrp" else "alphanumeric")
                        boxes = run_dot_matrix_ocr(crop, parent_offset=(float(x1), float(y1)), expected_field=exp_field, engine_mgr=engine_mgr)
                        for b in boxes:
                            norm_t = b.text.strip().lower()
                            c_tok = CanonicalToken(
                                text=b.text.strip(),
                                normalized_text=norm_t,
                                bbox=b.bbox,
                                ocr_confidence=b.confidence,
                                engine=b.engine,
                                variant=b.variant,
                                token_type="word",
                            )
                            token_store.word_tokens.append(c_tok)
                            reocr_tokens_added = True

            # If new tokens were added, re-run layout analysis
            if reocr_tokens_added:
                layout_struct, field_assignments = analyze_label_layout(token_store)

        # Convert field assignments to FieldCandidate objects
        for f_name, (lbl, val, p_score, l_conf) in field_assignments.items():
            layout_candidates[f_name] = FieldCandidate(
                field_name=f_name,
                value=val.text,
                raw_text=val.text,
                anchor_text=lbl.text,
                anchor_bbox=lbl.bbox,
                value_bbox=val.bbox,
                source="layout_association",
                ocr_confidence=val.ocr_confidence,
                field_score=p_score,
                layout_confidence=l_conf,
            )

    # -------------------------------------------------------------
    # 2. Product Name
    # -------------------------------------------------------------
    prod_match = extract_product_name(lines)
    if prod_match:
        p_val, p_conf, p_bbox = prod_match
        extracted_fields["product_name"] = p_val
        confidence_dict["product_name"] = round(p_conf, 2)
        field_details["product_name"] = {
            "value": p_val,
            "ocr_confidence": round(p_conf, 2),
            "field_confidence": round(p_conf, 2),
            "final_confidence": round(p_conf, 2),
            "status": "verified" if p_conf >= config.CONFIDENCE_HIGH else "needs_recheck",
            "source": "top_prominent_line",
            "bbox": p_bbox.to_dict() if p_bbox else None,
        }
    else:
        extracted_fields["product_name"] = None
        confidence_dict["product_name"] = 0.0
        uncertain_fields.append("product_name")
        field_details["product_name"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 3. Dedicated MRP Extraction Pipeline
    # -------------------------------------------------------------
    best_mrp, mrp_summary = extract_mrp_reliably(
        token_store,
        image=image,
        engine_mgr=engine_mgr,
        layout_candidate=layout_candidates.get("mrp"),
    )
    if best_mrp and best_mrp.value:
        extracted_fields["mrp"] = best_mrp.value
        confidence_dict["mrp"] = round(best_mrp.final_confidence, 2)
        mrp_dict = best_mrp.to_dict()
        if mrp_summary:
            mrp_dict["candidate_summary"] = mrp_summary
        field_details["mrp"] = mrp_dict
        if best_mrp.status != "verified":
            uncertain_fields.append("mrp")
        validation_notes.append(f"mrp: Plausible retail price ({best_mrp.value})")
    else:
        extracted_fields["mrp"] = None
        confidence_dict["mrp"] = 0.0
        uncertain_fields.append("mrp")
        field_details["mrp"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
            "notes": "No verified or plausible MRP candidate found",
            "candidate_summary": mrp_summary,
        }

    # -------------------------------------------------------------
    # 4. Dates (Manufacturing & Expiry) - ZERO Chronology Swapping
    # -------------------------------------------------------------
    best_mfg, best_exp, date_notes = extract_dates_reliably(token_store, layout_candidates=layout_candidates)
    validation_notes.extend(date_notes)

    # Manufacturing Date
    if best_mfg and best_mfg.value:
        extracted_fields["manufacturing_date"] = best_mfg.value
        confidence_dict["manufacturing_date"] = round(best_mfg.final_confidence, 2)
        field_details["manufacturing_date"] = best_mfg.to_dict()
        if best_mfg.status != "verified":
            uncertain_fields.append("manufacturing_date")
    else:
        extracted_fields["manufacturing_date"] = None
        confidence_dict["manufacturing_date"] = 0.0
        uncertain_fields.append("manufacturing_date")
        field_details["manufacturing_date"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # Expiry Date
    if best_exp and best_exp.value:
        extracted_fields["expiry_date"] = best_exp.value
        confidence_dict["expiry_date"] = round(best_exp.final_confidence, 2)
        field_details["expiry_date"] = best_exp.to_dict()
        if best_exp.status != "verified":
            uncertain_fields.append("expiry_date")
    else:
        extracted_fields["expiry_date"] = None
        confidence_dict["expiry_date"] = 0.0
        uncertain_fields.append("expiry_date")
        field_details["expiry_date"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 5. Net Quantity
    # -------------------------------------------------------------
    best_qty, qty_summary = extract_quantity_reliably(token_store, layout_candidate=layout_candidates.get("net_quantity"))
    if best_qty and best_qty.value:
        extracted_fields["net_quantity"] = best_qty.value
        confidence_dict["net_quantity"] = round(best_qty.final_confidence, 2)
        qty_dict = best_qty.to_dict()
        if qty_summary:
            qty_dict["candidate_summary"] = qty_summary
        field_details["net_quantity"] = qty_dict
        if best_qty.status != "verified":
            uncertain_fields.append("net_quantity")
        validation_notes.append("net_quantity: Conforms to Legal Metrology packaged commodity units")
    else:
        extracted_fields["net_quantity"] = None
        confidence_dict["net_quantity"] = 0.0
        uncertain_fields.append("net_quantity")
        field_details["net_quantity"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 6. Batch Number
    # -------------------------------------------------------------
    best_batch, batch_summary = extract_batch_reliably(token_store, layout_candidate=layout_candidates.get("batch_number"))
    if best_batch and best_batch.value:
        extracted_fields["batch_number"] = best_batch.value
        confidence_dict["batch_number"] = round(best_batch.final_confidence, 2)
        batch_dict = best_batch.to_dict()
        if batch_summary:
            batch_dict["candidate_summary"] = batch_summary
        field_details["batch_number"] = batch_dict
        if best_batch.status != "verified":
            uncertain_fields.append("batch_number")
    else:
        extracted_fields["batch_number"] = None
        confidence_dict["batch_number"] = 0.0
        uncertain_fields.append("batch_number")
        field_details["batch_number"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 7. License Number / FSSAI
    # -------------------------------------------------------------
    best_lic, lic_summary = extract_license_reliably(token_store, layout_candidate=layout_candidates.get("license_number"))
    if best_lic and best_lic.value:
        extracted_fields["license_number"] = best_lic.value
        confidence_dict["license_number"] = round(best_lic.final_confidence, 2)
        lic_dict = best_lic.to_dict()
        if lic_summary:
            lic_dict["candidate_summary"] = lic_summary
        field_details["license_number"] = lic_dict
        if best_lic.status != "verified":
            uncertain_fields.append("license_number")
        if len(best_lic.value) == 14 and best_lic.value.isdigit():
            validation_notes.append("license_number: Valid 14-digit FSSAI registration structure")
        else:
            validation_notes.append("license_number: Valid state AYUSH/manufacturing license pattern")
    else:
        extracted_fields["license_number"] = None
        confidence_dict["license_number"] = 0.0
        uncertain_fields.append("license_number")
        field_details["license_number"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 8. Unit Sale Price (USP)
    # -------------------------------------------------------------
    best_usp, usp_summary = extract_usp_reliably(
        token_store,
        mrp_candidate=best_mrp,
        layout_candidate=layout_candidates.get("unit_sale_price"),
    )
    if best_usp and best_usp.value:
        extracted_fields["unit_sale_price"] = best_usp.value
        confidence_dict["unit_sale_price"] = round(best_usp.final_confidence, 2)
        usp_dict = best_usp.to_dict()
        if usp_summary:
            usp_dict["candidate_summary"] = usp_summary
        field_details["unit_sale_price"] = usp_dict
        if best_usp.status != "verified":
            uncertain_fields.append("unit_sale_price")
    else:
        extracted_fields["unit_sale_price"] = None
        confidence_dict["unit_sale_price"] = 0.0
        uncertain_fields.append("unit_sale_price")
        field_details["unit_sale_price"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 9. Manufacturer
    # -------------------------------------------------------------
    mfg_comp = extract_manufacturer(lines)
    if mfg_comp:
        m_val, m_conf, m_bbox = mfg_comp
        extracted_fields["manufacturer"] = m_val
        confidence_dict["manufacturer"] = round(m_conf, 2)
        field_details["manufacturer"] = {
            "value": m_val,
            "ocr_confidence": round(m_conf, 2),
            "field_confidence": round(m_conf, 2),
            "final_confidence": round(m_conf, 2),
            "status": "verified" if m_conf >= config.CONFIDENCE_HIGH else "needs_recheck",
            "source": "corporate_suffix_match",
            "bbox": m_bbox.to_dict() if m_bbox else None,
        }
    else:
        extracted_fields["manufacturer"] = None
        confidence_dict["manufacturer"] = 0.0
        uncertain_fields.append("manufacturer")
        field_details["manufacturer"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 10. Customer Care
    # -------------------------------------------------------------
    full_text = " ".join(line.text for line in lines)
    cc_match = patterns.extract_customer_care(full_text)
    if cc_match:
        cc_val, cc_conf = cc_match
        extracted_fields["customer_care"] = cc_val
        confidence_dict["customer_care"] = round(cc_conf, 2)
        field_details["customer_care"] = {
            "value": cc_val,
            "ocr_confidence": round(cc_conf, 2),
            "field_confidence": round(cc_conf, 2),
            "final_confidence": round(cc_conf, 2),
            "status": "verified" if cc_conf >= config.CONFIDENCE_HIGH else "needs_recheck",
            "source": "contact_pattern_match",
        }
    else:
        extracted_fields["customer_care"] = None
        confidence_dict["customer_care"] = 0.0
        field_details["customer_care"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 11. Country of Origin
    # -------------------------------------------------------------
    country_val = None
    country_conf = 0.0
    country_bbox = None
    for line in lines:
        c_ext = patterns.extract_country_of_origin(line.text)
        if c_ext:
            country_val, country_conf = c_ext
            country_bbox = line.bbox
            break

    if country_val:
        extracted_fields["country_of_origin"] = country_val
        confidence_dict["country_of_origin"] = round(country_conf, 2)
        field_details["country_of_origin"] = {
            "value": country_val,
            "ocr_confidence": round(country_conf, 2),
            "field_confidence": round(country_conf, 2),
            "final_confidence": round(country_conf, 2),
            "status": "verified",
            "source": "country_pattern_match",
            "bbox": country_bbox.to_dict() if country_bbox else None,
        }
    else:
        extracted_fields["country_of_origin"] = None
        confidence_dict["country_of_origin"] = 0.0
        field_details["country_of_origin"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # -------------------------------------------------------------
    # 12. Manufacturer Address
    # -------------------------------------------------------------
    addr_val = None
    addr_conf = 0.0
    addr_bbox = None
    for line in lines:
        if prod_match and line.text == prod_match[0]:
            continue
        if mfg_comp and line.text == mfg_comp[0]:
            continue
        a_ext = patterns.extract_address_from_text(line.text)
        if a_ext:
            addr_val, addr_conf = a_ext
            addr_bbox = line.bbox
            break

    if addr_val:
        extracted_fields["manufacturer_address"] = addr_val
        confidence_dict["manufacturer_address"] = round(addr_conf, 2)
        field_details["manufacturer_address"] = {
            "value": addr_val,
            "ocr_confidence": round(addr_conf, 2),
            "field_confidence": round(addr_conf, 2),
            "final_confidence": round(addr_conf, 2),
            "status": "verified" if addr_conf >= config.CONFIDENCE_HIGH else "needs_recheck",
            "source": "address_pattern_match",
            "bbox": addr_bbox.to_dict() if addr_bbox else None,
        }
    else:
        extracted_fields["manufacturer_address"] = None
        confidence_dict["manufacturer_address"] = 0.0
        field_details["manufacturer_address"] = {
            "value": None,
            "ocr_confidence": 0.0,
            "field_confidence": 0.0,
            "final_confidence": 0.0,
            "status": "not_detected",
        }

    # Deduplicate uncertain fields
    uncertain_fields = sorted(list(set(uncertain_fields)))

    result = {
        "image": image_filename,
        "ocr_status": "success",
        "fields": extracted_fields,
        "confidence": confidence_dict,
        "uncertain_fields": uncertain_fields,
        "validation_notes": validation_notes,
        "field_details": field_details,
    }

    # Attach layout diagnostics
    if layout_struct is not None:
        result["layout"] = layout_struct.to_dict()
        if (config.DEBUG_VISUALIZATION_ENABLED or getattr(config, "VISUALIZE", False)) and image is not None:
            draw_layout_debug_image(image, layout_struct, image_filename)

    return result
