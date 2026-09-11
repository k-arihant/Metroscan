"""
Field Rankers for Packaged Product Compliance Fields:
Manufacturing Date, Expiry Date, Net Quantity, Batch Number, License Number, and Unit Sale Price.
Enforces semantic anchor association, negative classification, and strict rejection of chronology-based swapping.
"""
from typing import List, Tuple, Optional, Dict, Any
import re

import config
from src.extraction import patterns, validator
from src.extraction.tokens import CanonicalToken, OCRTokenStore
from src.extraction.candidate import FieldCandidate
from src.extraction.field_classifier import (
    looks_like_date,
    looks_like_phone,
    looks_like_fssai,
    looks_like_license,
    looks_like_batch,
    looks_like_quantity,
    looks_like_unit_sale_price,
    evaluate_bbox_quality,
)
from src.extraction.decision_engine import arbitrate_candidates

# -------------------------------------------------------------------------
# Semantic Anchor Definitions
# -------------------------------------------------------------------------
MFG_ANCHORS = [
    re.compile(r'\b(?:mfg(?:\.|\s*date)?|mfd(?:\.|\s*date)?|manufactured|packed\s*(?:on|date)?|pkd(?:\.|\s*date)?|date\s*of\s*(?:mfg|packaging|packing))\b', re.IGNORECASE),
]

EXP_ANCHORS = [
    re.compile(r'\b(?:exp(?:\.|\s*date)?|use\s*by|best\s*before|expiry\s*(?:date)?)\b', re.IGNORECASE),
]

QTY_ANCHORS = [
    re.compile(r'\b(?:net\s*(?:quantity|weight|wt|vol|content)?|qty|weight)\b', re.IGNORECASE),
]

BATCH_ANCHORS = [
    re.compile(r'\b(?:batch(?:\s*no\.?)?|lot(?:\s*no\.?)?|b\.?\s*no\.?|machine\s*code)\b', re.IGNORECASE),
]

LIC_ANCHORS = [
    re.compile(r'\b(?:fssai|lic(?:\.|\s*no\.?)?|regn(?:\.|\s*no\.?)?|license)\b', re.IGNORECASE),
]

USP_ANCHORS = [
    re.compile(r'\b(?:usp|unit\s*sale\s*price)\b', re.IGNORECASE),
]


# =========================================================================
# 1. DATES (MFG & EXP) - ZERO CHRONOLOGY SWAPPING
# =========================================================================

def extract_dates_reliably(
    token_store: OCRTokenStore,
    layout_candidates: Optional[Dict[str, FieldCandidate]] = None,
) -> Tuple[Optional[FieldCandidate], Optional[FieldCandidate], List[str]]:
    """
    Extract manufacturing date and expiry date using explicit semantic anchors.
    Never swaps dates based on inverted chronology.
    Returns (best_mfg, best_exp, validation_notes).
    """
    notes: List[str] = []

    def find_date_candidates_for_anchors(anchors: List[re.Pattern], field_name: str) -> List[FieldCandidate]:
        candidates: List[FieldCandidate] = []

        # Priority candidate from layout association
        if layout_candidates and field_name in layout_candidates:
            l_cand = layout_candidates[field_name]
            ext = patterns.extract_date(l_cand.value) or patterns.extract_date(l_cand.raw_text)
            if ext:
                l_cand.value = ext[0]
                l_cand.field_score = 90.0 + (ext[1] * 10.0)
                candidates.append(l_cand)

        matching_lines = []
        for line in token_store.line_tokens:
            for anc in anchors:
                if anc.search(line.text):
                    matching_lines.append(line)
                    break

        # 1. Same-line search
        for line in matching_lines:
            extracted = patterns.extract_date(line.text)
            if extracted:
                val, pat_conf = extracted
                # Find child word box for exact date bbox
                val_box = line.bbox
                if line.child_tokens:
                    for cw in line.child_tokens:
                        if val in cw.text or re.search(r'\d{2,4}', cw.text):
                            val_box = cw.bbox
                            break

                candidates.append(
                    FieldCandidate(
                        field_name=field_name,
                        value=val,
                        raw_text=line.text,
                        anchor_text=line.text,
                        anchor_bbox=line.bbox,
                        value_bbox=val_box,
                        source="same_line",
                        ocr_confidence=line.ocr_confidence,
                        field_score=85.0 + (pat_conf * 10.0),
                    )
                )

        # 2. Adjacent downward/rightward search from anchor
        for line in matching_lines:
            # Right adjacent
            right_tokens = token_store.find_tokens_right_of(line.bbox, max_h_distance=line.bbox.height * 8)
            for dist, rt in right_tokens[:4]:
                ext = patterns.extract_date(rt.text)
                if ext:
                    val, pat_conf = ext
                    candidates.append(
                        FieldCandidate(
                            field_name=field_name,
                            value=val,
                            raw_text=rt.text,
                            anchor_text=line.text,
                            anchor_bbox=line.bbox,
                            value_bbox=rt.bbox,
                            source="right_adjacent",
                            ocr_confidence=rt.ocr_confidence,
                            field_score=75.0 + (pat_conf * 10.0) - (dist / 100.0),
                        )
                    )

            # Below adjacent
            below_tokens = token_store.find_tokens_below(line.bbox, max_v_distance=line.bbox.height * 5)
            for dist, bt in below_tokens[:4]:
                ext = patterns.extract_date(bt.text)
                if ext:
                    val, pat_conf = ext
                    candidates.append(
                        FieldCandidate(
                            field_name=field_name,
                            value=val,
                            raw_text=bt.text,
                            anchor_text=line.text,
                            anchor_bbox=line.bbox,
                            value_bbox=bt.bbox,
                            source="below_adjacent",
                            ocr_confidence=bt.ocr_confidence,
                            field_score=70.0 + (pat_conf * 10.0) - (dist / 100.0),
                        )
                    )

        # 3. Global fallback (only if no anchor candidate)
        if not candidates:
            for line in token_store.line_tokens:
                ext = patterns.extract_date(line.text)
                if ext:
                    val, pat_conf = ext
                    candidates.append(
                        FieldCandidate(
                            field_name=field_name,
                            value=val,
                            raw_text=line.text,
                            anchor_text=None,
                            anchor_bbox=None,
                            value_bbox=line.bbox,
                            source="global_fallback",
                            ocr_confidence=line.ocr_confidence,
                            field_score=40.0 + (pat_conf * 10.0),
                            is_fallback=True,
                        )
                    )

        return candidates

    mfg_cands = find_date_candidates_for_anchors(MFG_ANCHORS, "manufacturing_date")
    exp_cands = find_date_candidates_for_anchors(EXP_ANCHORS, "expiry_date")

    # Filter out fallback candidates that collide with the other field's non-fallback choice
    has_anchored_mfg = any(not c.is_fallback for c in mfg_cands)
    has_anchored_exp = any(not c.is_fallback for c in exp_cands)

    if has_anchored_mfg and not has_anchored_exp:
        # Exclude mfg values from exp fallback
        mfg_vals = {c.value for c in mfg_cands if not c.is_fallback}
        exp_cands = [c for c in exp_cands if c.value not in mfg_vals]
    elif has_anchored_exp and not has_anchored_mfg:
        # Exclude exp values from mfg fallback
        exp_vals = {c.value for c in exp_cands if not c.is_fallback}
        mfg_cands = [c for c in mfg_cands if c.value not in exp_vals]
    elif not has_anchored_mfg and not has_anchored_exp:
        # Both only have fallback candidates!
        # Collect all unique dates found globally
        all_unique_dates = []
        seen = set()
        for c in mfg_cands:
            if c.value not in seen:
                seen.add(c.value)
                all_unique_dates.append(c)

        if len(all_unique_dates) == 1:
            # Only one date on package without anchor -> attribute to manufacturing_date, clear expiry_date
            mfg_cands = [all_unique_dates[0]]
            exp_cands = []
        elif len(all_unique_dates) >= 2:
            # Sort chronologically: earlier date to MFG, later date to EXP
            parsed_dates = []
            for c in all_unique_dates:
                dt = validator.parse_date_obj(c.value)
                if dt:
                    parsed_dates.append((dt, c))
            parsed_dates.sort(key=lambda x: x[0])
            if len(parsed_dates) >= 2:
                earlier_c = parsed_dates[0][1]
                later_c = parsed_dates[-1][1]
                earlier_c.field_name = "manufacturing_date"
                later_c.field_name = "expiry_date"
                mfg_cands = [earlier_c]
                exp_cands = [later_c]

    best_mfg, _ = arbitrate_candidates("manufacturing_date", mfg_cands)
    best_exp, _ = arbitrate_candidates("expiry_date", exp_cands)

    # If both ended up with the identical date value and at least one is fallback, clear the fallback
    if best_mfg and best_exp and best_mfg.value == best_exp.value:
        if getattr(best_exp, "is_fallback", False):
            best_exp = None
        elif getattr(best_mfg, "is_fallback", False):
            best_mfg = None

    # -------------------------------------------------------------
    # Cross-Date Chronology Check (NO SWAPPING)
    # -------------------------------------------------------------
    if best_mfg and best_exp and best_mfg.value and best_exp.value:
        mfg_dt = validator.parse_date_obj(best_mfg.value)
        exp_dt = validator.parse_date_obj(best_exp.value)

        if mfg_dt and exp_dt:
            if mfg_dt > exp_dt:
                # Chronology Conflict! Do NOT swap dates!
                notes.append(
                    f"CRITICAL DATE CONFLICT: Manufacturing date ({best_mfg.value}) is AFTER Expiry date ({best_exp.value}). "
                    f"Chronology inversion detected; flagged as needs_recheck."
                )
                best_mfg.status = "needs_recheck"
                best_exp.status = "needs_recheck"
                best_mfg.final_confidence = min(best_mfg.final_confidence, 0.45)
                best_exp.final_confidence = min(best_exp.final_confidence, 0.45)
                best_mfg.decision_reasons.append("Date chronology conflict with expiry date")
                best_exp.decision_reasons.append("Date chronology conflict with manufacturing date")
            else:
                notes.append(f"Date chronology verified: Mfg ({best_mfg.value}) <= Exp ({best_exp.value})")

    return best_mfg, best_exp, notes


# =========================================================================
# 2. NET QUANTITY
# =========================================================================

def extract_quantity_reliably(
    token_store: OCRTokenStore,
    layout_candidate: Optional[FieldCandidate] = None,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Extract net quantity adhering strictly to Legal Metrology packaged commodity units.
    Rejects 0 l, dates, barcodes, phone numbers.
    """
    candidates: List[FieldCandidate] = []

    if layout_candidate:
        ext = patterns.extract_net_quantity(layout_candidate.value) or patterns.extract_net_quantity(layout_candidate.raw_text)
        if ext:
            val, _ = ext
            is_valid, validated_val, _, _ = validator.validate_net_quantity(val)
            if is_valid:
                layout_candidate.value = validated_val
                layout_candidate.field_score = 92.0
                candidates.append(layout_candidate)

    matching_lines = []
    for line in token_store.line_tokens:
        for anc in QTY_ANCHORS:
            if anc.search(line.text):
                matching_lines.append(line)
                break

    # 1. Search same line as Net Quantity anchor
    for line in matching_lines:
        ext = patterns.extract_net_quantity(line.text)
        if ext:
            val, pat_conf = ext
            # Check unit legality
            is_valid, validated_val, _, _ = validator.validate_net_quantity(val)
            if is_valid:
                candidates.append(
                    FieldCandidate(
                        field_name="net_quantity",
                        value=validated_val,
                        raw_text=line.text,
                        anchor_text=line.text,
                        anchor_bbox=line.bbox,
                        value_bbox=line.bbox,
                        source="same_line",
                        ocr_confidence=line.ocr_confidence,
                        field_score=90.0,
                    )
                )

    # 2. Search adjacent tokens
    for line in matching_lines:
        right_tokens = token_store.find_tokens_right_of(line.bbox, max_h_distance=line.bbox.height * 8)
        for dist, rt in right_tokens[:4]:
            ext = patterns.extract_net_quantity(rt.text)
            if ext:
                val, _ = ext
                is_valid, validated_val, _, _ = validator.validate_net_quantity(val)
                if is_valid:
                    candidates.append(
                        FieldCandidate(
                            field_name="net_quantity",
                            value=validated_val,
                            raw_text=rt.text,
                            anchor_text=line.text,
                            anchor_bbox=line.bbox,
                            value_bbox=rt.bbox,
                            source="right_adjacent",
                            ocr_confidence=rt.ocr_confidence,
                            field_score=80.0 - (dist / 100.0),
                        )
                    )

    # 3. Global scan across all lines
    if not candidates:
        for line in token_store.line_tokens:
            ext = patterns.extract_net_quantity(line.text)
            if ext:
                val, _ = ext
                is_valid, validated_val, _, _ = validator.validate_net_quantity(val)
                if is_valid:
                    candidates.append(
                        FieldCandidate(
                            field_name="net_quantity",
                            value=validated_val,
                            raw_text=line.text,
                            anchor_text=None,
                            anchor_bbox=None,
                            value_bbox=line.bbox,
                            source="global_fallback",
                            ocr_confidence=line.ocr_confidence,
                            field_score=55.0,
                            is_fallback=True,
                        )
                    )

    # Rejection of invalid quantities like "0 l", "0 g"
    valid_candidates = []
    for c in candidates:
        # Check non-positive
        m = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', c.value)
        if m and float(m.group(1)) <= 0.0:
            continue
        valid_candidates.append(c)

    return arbitrate_candidates("net_quantity", valid_candidates)


# =========================================================================
# 3. BATCH NUMBER
# =========================================================================

def extract_batch_reliably(
    token_store: OCRTokenStore,
    layout_candidate: Optional[FieldCandidate] = None,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Extract batch/lot number using explicit anchors and alphanumeric patterns.
    Rejects anchor words themselves (e.g. 'BATCHNUMMER'), dates, MRP, and phone numbers.
    """
    candidates: List[FieldCandidate] = []

    if layout_candidate:
        ext = patterns.extract_batch_number(layout_candidate.value) or patterns.extract_batch_number(layout_candidate.raw_text)
        if ext:
            val, pat_conf = ext
            if val.upper() not in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER"}:
                layout_candidate.value = val
                layout_candidate.field_score = 90.0 + (pat_conf * 10.0)
                candidates.append(layout_candidate)

    matching_lines = []
    for line in token_store.line_tokens:
        for anc in BATCH_ANCHORS:
            if anc.search(line.text):
                matching_lines.append(line)
                break

    # 1. Search same line
    for line in matching_lines:
        ext = patterns.extract_batch_number(line.text)
        if ext:
            val, pat_conf = ext
            # Reject if val is just the anchor word itself
            if val.upper() in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER", "CODE"}:
                continue
            candidates.append(
                FieldCandidate(
                    field_name="batch_number",
                    value=val,
                    raw_text=line.text,
                    anchor_text=line.text,
                    anchor_bbox=line.bbox,
                    value_bbox=line.bbox,
                    source="same_line",
                    ocr_confidence=line.ocr_confidence,
                    field_score=85.0 + (pat_conf * 10.0),
                )
            )

    # 2. Adjacent tokens (right or below)
    for line in matching_lines:
        # Right adjacent
        right_tokens = token_store.find_tokens_right_of(line.bbox, max_h_distance=line.bbox.height * 6)
        for dist, rt in right_tokens[:4]:
            ext = patterns.extract_batch_number(rt.text)
            if ext:
                val, pat_conf = ext
                if val.upper() not in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER"}:
                    candidates.append(
                        FieldCandidate(
                            field_name="batch_number",
                            value=val,
                            raw_text=rt.text,
                            anchor_text=line.text,
                            anchor_bbox=line.bbox,
                            value_bbox=rt.bbox,
                            source="right_adjacent",
                            ocr_confidence=rt.ocr_confidence,
                            field_score=80.0 + (pat_conf * 10.0) - (dist / 100.0),
                        )
                    )

        # Below adjacent
        below_tokens = token_store.find_tokens_below(line.bbox, max_v_distance=line.bbox.height * 4)
        for dist, bt in below_tokens[:4]:
            ext = patterns.extract_batch_number(bt.text)
            if ext:
                val, pat_conf = ext
                if val.upper() not in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER"}:
                    candidates.append(
                        FieldCandidate(
                            field_name="batch_number",
                            value=val,
                            raw_text=bt.text,
                            anchor_text=line.text,
                            anchor_bbox=line.bbox,
                            value_bbox=bt.bbox,
                            source="below_adjacent",
                            ocr_confidence=bt.ocr_confidence,
                            field_score=75.0 + (pat_conf * 10.0) - (dist / 100.0),
                        )
                    )

    # 3. Standalone alphanumeric batch codes across all lines
    if not candidates:
        for line in token_store.line_tokens:
            ext = patterns.extract_batch_number(line.text)
            if ext:
                val, pat_conf = ext
                if val.upper() not in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER"}:
                    # Reject pure numbers or dates
                    if not val.isdigit() and not re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', val):
                        candidates.append(
                            FieldCandidate(
                                field_name="batch_number",
                                value=val,
                                raw_text=line.text,
                                anchor_text=None,
                                anchor_bbox=None,
                                value_bbox=line.bbox,
                                source="global_fallback",
                                ocr_confidence=line.ocr_confidence,
                                field_score=50.0,
                                is_fallback=True,
                            )
                        )

    # Negative filter: batch must NOT look like a date or 10-digit phone
    filtered = []
    for c in candidates:
        is_d, _, _ = looks_like_date(c.value)
        is_ph, _, _ = looks_like_phone(c.value)
        if is_d or is_ph:
            continue
        filtered.append(c)

    return arbitrate_candidates("batch_number", filtered)


# =========================================================================
# 4. LICENSE / FSSAI NUMBER
# =========================================================================

def extract_license_reliably(
    token_store: OCRTokenStore,
    layout_candidate: Optional[FieldCandidate] = None,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Extract FSSAI or AYUSH manufacturing license with context enforcement.
    Rejects pure standalone numbers without license context.
    """
    candidates: List[FieldCandidate] = []

    if layout_candidate:
        ext = patterns.extract_license_number(layout_candidate.value) or patterns.extract_license_number(layout_candidate.raw_text)
        if ext:
            val, pat_conf = ext
            layout_candidate.value = val
            layout_candidate.field_score = 92.0 + (pat_conf * 10.0)
            candidates.append(layout_candidate)

    matching_lines = []
    for line in token_store.line_tokens:
        for anc in LIC_ANCHORS:
            if anc.search(line.text):
                matching_lines.append(line)
                break

    # 1. Same line as license anchor
    for line in matching_lines:
        ext = patterns.extract_license_number(line.text)
        if ext:
            val, pat_conf = ext
            candidates.append(
                FieldCandidate(
                    field_name="license_number",
                    value=val,
                    raw_text=line.text,
                    anchor_text=line.text,
                    anchor_bbox=line.bbox,
                    value_bbox=line.bbox,
                    source="same_line",
                    ocr_confidence=line.ocr_confidence,
                    field_score=90.0 + (pat_conf * 10.0),
                )
            )

    # 2. Adjacent search from license anchor
    for line in matching_lines:
        right_tokens = token_store.find_tokens_right_of(line.bbox, max_h_distance=line.bbox.height * 8)
        for dist, rt in right_tokens[:4]:
            ext = patterns.extract_license_number(rt.text)
            if ext:
                val, pat_conf = ext
                candidates.append(
                    FieldCandidate(
                        field_name="license_number",
                        value=val,
                        raw_text=rt.text,
                        anchor_text=line.text,
                        anchor_bbox=line.bbox,
                        value_bbox=rt.bbox,
                        source="right_adjacent",
                        ocr_confidence=rt.ocr_confidence,
                        field_score=80.0 + (pat_conf * 10.0) - (dist / 100.0),
                    )
                )

    # 3. 14-digit FSSAI pattern anywhere in text
    if not candidates:
        for line in token_store.line_tokens:
            ext = patterns.extract_license_number(line.text)
            if ext:
                val, pat_conf = ext
                # If it's a 14-digit number starting with 1 or 2
                digits = re.sub(r'\D', '', val)
                if len(digits) == 14 and digits[0] in ['1', '2']:
                    candidates.append(
                        FieldCandidate(
                            field_name="license_number",
                            value=digits,
                            raw_text=line.text,
                            anchor_text=None,
                            anchor_bbox=None,
                            value_bbox=line.bbox,
                            source="global_fallback",
                            ocr_confidence=line.ocr_confidence,
                            field_score=70.0,
                            is_fallback=True,
                        )
                    )

    # Negative filter: must not be a date
    filtered = [c for c in candidates if not looks_like_date(c.value)[0]]
    return arbitrate_candidates("license_number", filtered)


# =========================================================================
# 5. UNIT SALE PRICE (USP)
# =========================================================================

def extract_usp_reliably(
    token_store: OCRTokenStore,
    mrp_candidate: Optional[FieldCandidate] = None,
    layout_candidate: Optional[FieldCandidate] = None,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Extract unit sale price with rate/unit combination.
    Rejects values identical to MRP.
    """
    candidates: List[FieldCandidate] = []

    if layout_candidate:
        ext = patterns.extract_unit_sale_price(layout_candidate.value) or patterns.extract_unit_sale_price(layout_candidate.raw_text)
        if ext:
            val, pat_conf = ext
            layout_candidate.value = val
            layout_candidate.field_score = 90.0 + (pat_conf * 10.0)
            candidates.append(layout_candidate)

    matching_lines = []
    for line in token_store.line_tokens:
        for anc in USP_ANCHORS:
            if anc.search(line.text):
                matching_lines.append(line)
                break

    # 1. Search same line
    for line in matching_lines:
        ext = patterns.extract_unit_sale_price(line.text)
        if ext:
            val, pat_conf = ext
            candidates.append(
                FieldCandidate(
                    field_name="unit_sale_price",
                    value=val,
                    raw_text=line.text,
                    anchor_text=line.text,
                    anchor_bbox=line.bbox,
                    value_bbox=line.bbox,
                    source="same_line",
                    ocr_confidence=line.ocr_confidence,
                    field_score=85.0 + (pat_conf * 10.0),
                )
            )

    # 2. Adjacent tokens (right or below)
    for line in matching_lines:
        right_tokens = token_store.find_tokens_right_of(line.bbox, max_h_distance=line.bbox.height * 8)
        for dist, rt in right_tokens[:4]:
            ext = patterns.extract_unit_sale_price(rt.text)
            if ext:
                val, pat_conf = ext
                candidates.append(
                    FieldCandidate(
                        field_name="unit_sale_price",
                        value=val,
                        raw_text=rt.text,
                        anchor_text=line.text,
                        anchor_bbox=line.bbox,
                        value_bbox=rt.bbox,
                        source="right_adjacent",
                        ocr_confidence=rt.ocr_confidence,
                        field_score=80.0 + (pat_conf * 10.0) - (dist / 100.0),
                    )
                )

    # 3. Global scan for rate format: e.g. "0.55/g", "0.43/g", "2.22/ml"
    if not candidates:
        for line in token_store.line_tokens:
            ext = patterns.extract_unit_sale_price(line.text)
            if ext:
                val, pat_conf = ext
                # Standalone rate must contain a slash or unit
                if "/" in val or "per" in line.text.lower():
                    candidates.append(
                        FieldCandidate(
                            field_name="unit_sale_price",
                            value=val,
                            raw_text=line.text,
                            anchor_text=None,
                            anchor_bbox=None,
                            value_bbox=line.bbox,
                            source="global_fallback",
                            ocr_confidence=line.ocr_confidence,
                            field_score=65.0,
                            is_fallback=True,
                        )
                    )

    # Reject candidate if identical to MRP value
    filtered = []
    mrp_val = mrp_candidate.value if mrp_candidate else None
    for c in candidates:
        if mrp_val and (c.value == mrp_val or c.value.startswith(f"{mrp_val}/")):
            continue
        filtered.append(c)

    return arbitrate_candidates("unit_sale_price", filtered)
