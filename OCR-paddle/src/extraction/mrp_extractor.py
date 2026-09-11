"""
Dedicated MRP Extraction Pipeline.
Anchor detection, local neighborhood candidate generation, negative classification,
scoring, targeted re-OCR for faint/dot-matrix stamps, and candidate arbitration.
"""
from typing import List, Tuple, Optional, Dict, Any
import re
import cv2
import numpy as np

import config
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
    looks_like_barcode,
    evaluate_bbox_quality,
)
from src.extraction.decision_engine import arbitrate_candidates
from src.utils.geometry import BoundingBox, distance_between, is_horizontally_aligned
from src.ocr.dot_matrix import run_dot_matrix_ocr

# MRP Anchor regular expressions
MRP_EXPLICIT_ANCHOR = re.compile(
    r'\b(?:m\.?[rp]\.?[prb]\.?|mrr|mbp|m\.r\.p\.?|max(?:imum)?\s*retail\s*price|incl(?:usive)?\s*(?:of\s*all\s*)?taxes?|all\s*taxes)\b',
    re.IGNORECASE
)
# Currency marker must have word boundaries for rs and inr so it does not match inside words like 'calories' or 'first'
CURRENCY_ANCHOR = re.compile(
    r'(?:[₹]|(?:\b(?:rs\.?|inr)\b))',
    re.IGNORECASE
)

NUTRITION_EXCLUDE = re.compile(
    r'\b(?:nutrition|calorie|calories?|kcal|serving|dietary|protein|carbohydrate|fat|sugar|daily\s*value)\b',
    re.IGNORECASE
)

# Standard price patterns: 360.00, 430.00, 110/-, 38, 22.00, 699.00
PRICE_NUMBER_REGEX = re.compile(
    r'(?:[₹Rs.]\s*)?(\d+(?:\.\d{2})?)\s*(?:/-)?',
    re.IGNORECASE
)


def find_mrp_anchors(token_store: OCRTokenStore) -> List[Tuple[CanonicalToken, str]]:
    """
    Locate all MRP anchors in the token store.
    Returns: List of (anchor_token, anchor_type) where anchor_type is 'explicit' or 'currency'.
    """
    anchors = []
    # Search line tokens first (excluding nutritional tables)
    for line in token_store.line_tokens:
        if NUTRITION_EXCLUDE.search(line.text):
            continue
        if MRP_EXPLICIT_ANCHOR.search(line.text):
            anchors.append((line, "explicit"))
        elif CURRENCY_ANCHOR.search(line.text) and not any(k in line.text.lower() for k in ["usp", "unit", "weight", "net"]):
            anchors.append((line, "currency"))

    # Also check word tokens to get tight anchor boxes
    for word in token_store.word_tokens:
        if NUTRITION_EXCLUDE.search(word.text):
            continue
        if MRP_EXPLICIT_ANCHOR.search(word.text):
            anchors.append((word, "explicit"))
        elif CURRENCY_ANCHOR.search(word.text):
            anchors.append((word, "currency"))
    return anchors


def extract_price_candidates_from_text(
    text: str,
    ref_bbox: BoundingBox,
    source: str,
    anchor_text: Optional[str] = None,
    anchor_bbox: Optional[BoundingBox] = None,
    ocr_confidence: float = 0.8,
    child_tokens: Optional[List[CanonicalToken]] = None,
) -> List[FieldCandidate]:
    """Extract numeric price candidates from a string."""
    # Exclude nutritional tables
    if re.search(r'\b(nutrition|calorie|serving|protein|carb|sodium|fat|sugar)\b', text, re.IGNORECASE):
        return []

    candidates = []
    # Normalize European/OCR comma decimal e.g. "120,00" -> "120.00"
    text_norm = re.sub(r'(\d+),(\d{2})\b', r'\1.\2', text)
    # Normalize OCR double-O e.g. "22 OO taxes" -> "22.00 taxes"
    text_norm = re.sub(r'\b(\d+)\s+[Oo]{2}\b', r'\1.00', text_norm)

    # 1. Check for explicit MRP pattern: "MRP ₹360.00", "MRP: 430.00", "Mrr, OF 120,00"
    explicit_pat = re.search(
        r'(?:m\.?[rp]\.?[prb]\.?|mrr|mbp|m\.r\.p\.?|max(?:imum)?\s*retail\s*price)[\s:₹Rs.,of]*(\d+(?:\.\d{2})?)\s*(?:/-)?',
        text_norm,
        re.IGNORECASE
    )
    if explicit_pat:
        val_str = explicit_pat.group(1)
        val_box = ref_bbox
        # Find exact child word box if available
        if child_tokens:
            for cw in child_tokens:
                cw_norm = re.sub(r'(\d+),(\d{2})\b', r'\1.\2', cw.text)
                cw_norm = re.sub(r'\b(\d+)\s+[Oo]{2}\b', r'\1.00', cw_norm)
                if (
                    val_str in cw.text
                    or val_str in cw_norm
                    or val_str.replace('.', ',') in cw.text
                    or val_str.split('.')[0] == cw.text
                    or cw.text in val_str
                ):
                    val_box = cw.bbox
                    break

        candidates.append(
            FieldCandidate(
                field_name="mrp",
                value=val_str,
                raw_text=text,
                anchor_text=anchor_text or "MRP",
                anchor_bbox=anchor_bbox or ref_bbox,
                value_bbox=val_box,
                source=source,
                ocr_confidence=ocr_confidence,
            )
        )

    # 1b. Check for tax/inclusive pattern: "22.00 taxes", "360.00 incl taxes"
    tax_pat = re.search(
        r'(\d+(?:\.\d{2})?)\s*(?:/-)?\s*(?:[oO]{2}\s*)?(?:incl\.?|inclusive|of\s*all\s*taxes|taxes)\b',
        text_norm,
        re.IGNORECASE
    )
    if tax_pat:
        val_str = tax_pat.group(1)
        if not any(c.value == val_str for c in candidates):
            val_box = ref_bbox
            if child_tokens:
                for cw in child_tokens:
                    cw_norm = re.sub(r'(\d+),(\d{2})\b', r'\1.\2', cw.text)
                    cw_norm = re.sub(r'\b(\d+)\s+[Oo]{2}\b', r'\1.00', cw_norm)
                    if (
                        val_str in cw.text
                        or val_str in cw_norm
                        or val_str.replace('.', ',') in cw.text
                        or val_str.split('.')[0] == cw.text
                        or cw.text in val_str
                    ):
                        val_box = cw.bbox
                        break
            candidates.append(
                FieldCandidate(
                    field_name="mrp",
                    value=val_str,
                    raw_text=text,
                    anchor_text=anchor_text or "MRP (taxes)",
                    anchor_bbox=anchor_bbox or ref_bbox,
                    value_bbox=val_box,
                    source=source,
                    ocr_confidence=ocr_confidence,
                )
            )

    # 2. Extract numeric tokens with currency prefix or standalone
    num_matches = re.finditer(r'(?:(?:₹|rs\.?|inr)[\s.]*)?(\d+(?:\.\d{2})?)\s*(?:/-)?', text_norm, re.IGNORECASE)
    for m in num_matches:
        num_str = m.group(1)
        # Skip 4-digit calendar years
        if num_str in {"2024", "2025", "2026", "2027", "2028", "2029", "2030"}:
            continue
        # Skip already added explicit value
        if any(c.value == num_str for c in candidates):
            continue

        val_box = ref_bbox
        if child_tokens:
            for cw in child_tokens:
                cw_norm = re.sub(r'(\d+),(\d{2})\b', r'\1.\2', cw.text)
                cw_norm = re.sub(r'\b(\d+)\s+[Oo]{2}\b', r'\1.00', cw_norm)
                if (
                    num_str in cw.text
                    or num_str in cw_norm
                    or num_str.replace('.', ',') in cw.text
                    or num_str.split('.')[0] == cw.text
                    or cw.text in num_str
                ):
                    val_box = cw.bbox
                    break

        candidates.append(
            FieldCandidate(
                field_name="mrp",
                value=num_str,
                raw_text=text,
                anchor_text=anchor_text,
                anchor_bbox=anchor_bbox,
                value_bbox=val_box,
                source=source,
                ocr_confidence=ocr_confidence,
            )
        )

    return candidates


def score_mrp_candidate(
    cand: FieldCandidate,
    image_shape: Tuple[int, int],
    token_store: OCRTokenStore,
) -> float:
    """
    Calculate transparent evidence score for an MRP candidate.
    Applies positive feature weights and strict negative penalties.
    """
    score = 0.0
    evidence: Dict[str, Any] = {
        "mrp_keyword_nearby": False,
        "currency_symbol_nearby": False,
        "same_line": False,
        "cross_ocr_agreement": False,
        "looks_like_date": False,
        "looks_like_phone": False,
        "looks_like_fssai": False,
        "looks_like_batch": False,
        "looks_like_quantity": False,
        "looks_like_usp": False,
    }
    reasons: List[str] = []

    # -------------------------------------------------------------
    # 1. Negative Semantic Classification (FATAL CHECKS)
    # -------------------------------------------------------------
    # Date check: value directly matches date pattern, or integer value is a component of a date in context
    is_date, d_conf, d_type = looks_like_date(cand.value)
    if not is_date and '.' not in cand.value:
        is_date_ctx, d_conf, d_type = looks_like_date(cand.raw_text)
        if is_date_ctx:
            date_matches = re.findall(r'\b(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}[-/\.]\d{4}|\d{4})\b', cand.raw_text)
            for dm in date_matches:
                parts = re.split(r'[-/\.]', dm)
                if cand.value in parts:
                    is_date = True
                    break
    if is_date:
        evidence["looks_like_date"] = True
        score += config.PENALTY_LOOKS_LIKE_DATE
        reasons.append(f"Penalized: resembles calendar date ({d_type}, conf={d_conf:.2f})")

    # Phone check
    is_ph, ph_conf, ph_type = looks_like_phone(cand.raw_text)
    if is_ph:
        evidence["looks_like_phone"] = True
        score += config.PENALTY_LOOKS_LIKE_PHONE
        reasons.append("Penalized: resembles customer care phone number")

    # FSSAI check
    is_fs, fs_conf, fs_type = looks_like_fssai(cand.raw_text)
    if is_fs:
        evidence["looks_like_fssai"] = True
        score += config.PENALTY_LOOKS_LIKE_FSSAI
        reasons.append("Penalized: resembles FSSAI license number")

    # Quantity check: value resembles quantity or is followed by unit of measure in raw text
    is_qty, q_conf, q_type = looks_like_quantity(cand.value)
    if not is_qty:
        if re.search(rf'\b{re.escape(cand.value)}\s*(?:g|gm|gms|kg|ml|l|ltr|pcs|count|tab|cap)\b', cand.raw_text, re.IGNORECASE):
            is_qty = True
            q_conf = 0.95
            q_type = "candidate_followed_by_quantity_unit"
        elif looks_like_quantity(cand.raw_text)[0] and len(cand.value) <= 3 and '.' not in cand.value:
            is_qty = True
            q_conf = 0.85
            q_type = "integer_in_quantity_context"
    if is_qty:
        evidence["looks_like_quantity"] = True
        score += config.PENALTY_LOOKS_LIKE_QUANTITY
        reasons.append(f"Penalized: resembles packaged commodity net quantity ({q_type})")

    # USP check
    is_usp, u_conf, u_type = looks_like_unit_sale_price(cand.raw_text)
    if is_usp:
        evidence["looks_like_usp"] = True
        score += config.PENALTY_LOOKS_LIKE_USP
        reasons.append("Penalized: resembles unit sale price fraction")

    # Barcode check
    is_bc, bc_conf, _ = looks_like_barcode(cand.value)
    if is_bc:
        score += -30.0
        reasons.append("Penalized: matches unadorned barcode digits")

    # Nutrition / calorie table check
    if NUTRITION_EXCLUDE.search(cand.raw_text):
        score += -45.0
        reasons.append("Penalized: text contains nutritional or calorie table reference")

    # -------------------------------------------------------------
    # 2. Bounding Box Geometry Quality
    # -------------------------------------------------------------
    if cand.value_bbox:
        bbox_pen, bbox_notes = evaluate_bbox_quality(cand.value_bbox, image_shape, cand.value)
        score += bbox_pen
        reasons.extend(bbox_notes)

    # -------------------------------------------------------------
    # 3. Source & Spatial Alignment Bonuses
    # -------------------------------------------------------------
    if cand.source == "same_line":
        score += config.MRP_WEIGHT_SAME_LINE
        evidence["same_line"] = True
        reasons.append("Numeric candidate found on same line as MRP anchor")

    elif cand.source in {"right_adjacent", "below_adjacent", "above_adjacent"}:
        score += config.MRP_WEIGHT_SPATIAL_ADJACENT
        reasons.append(f"Candidate directly {cand.source.replace('_', ' ')} to anchor")

    elif cand.source == "reocr":
        if cand.ocr_confidence >= 0.55:
            score += 32.0 * cand.ocr_confidence
            reasons.append(f"Candidate verified by targeted patch re-OCR (conf={cand.ocr_confidence:.2f})")
        elif cand.ocr_confidence < 0.45:
            score += -25.0
            reasons.append(f"Penalized: low confidence patch re-OCR fragment (conf={cand.ocr_confidence:.2f})")
        else:
            score += 5.0
            reasons.append(f"Marginal confidence patch re-OCR fragment (conf={cand.ocr_confidence:.2f})")

    elif cand.source == "layout_association":
        layout_bonus = 30.0
        if cand.layout_confidence is not None:
            layout_bonus += 15.0 * cand.layout_confidence
        score += layout_bonus
        reasons.append(f"Global layout table assignment (layout_conf={cand.layout_confidence if cand.layout_confidence else 0.8:.2f})")

    elif cand.source == "global_fallback":
        score += config.PENALTY_GLOBAL_FALLBACK
        cand.is_fallback = True
        reasons.append("Penalized: global fallback without semantic anchor association")

    # Spatial alignment bonus for adjacent/same line candidates
    if cand.source in {"right_adjacent", "same_line"} and cand.anchor_bbox and cand.value_bbox:
        y_diff = abs(cand.value_bbox.center_y - cand.anchor_bbox.center_y)
        if y_diff <= max(cand.anchor_bbox.height, 15.0) * 0.6:
            score += 15.0
            reasons.append("Exact horizontal alignment with MRP anchor")

    # -------------------------------------------------------------
    # 4. Anchor & Currency Proximity
    # -------------------------------------------------------------
    if cand.anchor_text:
        if MRP_EXPLICIT_ANCHOR.search(cand.anchor_text):
            score += config.MRP_WEIGHT_KEYWORD_NEARBY
            evidence["mrp_keyword_nearby"] = True
            reasons.append("Explicit MRP label anchor detected")
        elif CURRENCY_ANCHOR.search(cand.anchor_text):
            score += config.MRP_WEIGHT_CURRENCY_NEARBY
            evidence["currency_symbol_nearby"] = True
            reasons.append("Currency symbol (₹/Rs) anchor detected")

    if CURRENCY_ANCHOR.search(cand.raw_text):
        score += config.MRP_WEIGHT_CURRENCY_NEARBY
        evidence["currency_symbol_nearby"] = True

    # Tax / inclusive indicator bonus
    if re.search(r'\b(taxes?|incl\.?|inclusive|of\s*all\s*taxes)\b', cand.raw_text, re.IGNORECASE):
        score += 15.0
        reasons.append("Co-occurs with tax/inclusive indicator (e.g. incl of all taxes)")

    # -------------------------------------------------------------
    # 5. Price Plausibility & Format
    # -------------------------------------------------------------
    try:
        val_float = float(cand.value)
        if 1.0 <= val_float <= 50000.0:
            score += config.MRP_WEIGHT_PRICE_FORMAT
            # Bonus for standard 2-decimal format e.g. 360.00
            if '.' in cand.value and len(cand.value.split('.')[1]) == 2:
                score += 20.0
                reasons.append("Standard two-decimal currency format (.00)")
            elif len(cand.value) == 1:
                score += -20.0
                reasons.append("Penalized: isolated single digit unlikely to be packaged commodity MRP")
        else:
            score += -30.0
            reasons.append(f"Price plausibility failed: {val_float} out of range [1, 50000]")
    except ValueError:
        score += -50.0
        reasons.append("Non-numeric price string")

    # Consensus bonus
    if getattr(cand, "consensus_count", 1) >= 2:
        score += config.MRP_WEIGHT_OCR_CONSENSUS
        evidence["cross_ocr_agreement"] = True
        reasons.append("Multiple OCR passes/engines agree on text")

    cand.field_score = max(0.0, score)
    cand.evidence = evidence
    cand.decision_reasons = reasons

    return cand.field_score


def targeted_mrp_reocr(
    image: np.ndarray,
    anchor_bbox: BoundingBox,
    engine_mgr: Any,
) -> List[FieldCandidate]:
    """
    Perform high-resolution targeted patch re-OCR around an MRP anchor.
    Uses dedicated Stage 2 dot-matrix pipeline (upscaling, CLAHE, morphological dot bridging).
    """
    img_h, img_w = image.shape[:2]
    h_anchor = max(anchor_bbox.height, 20.0)

    # Window covering line above through line below
    y1 = max(0, int(anchor_bbox.y_min - h_anchor * 1.1))
    y2 = min(img_h, int(anchor_bbox.y_max + h_anchor * 1.3))
    x1 = max(0, int(anchor_bbox.x_min - 25))
    x2 = min(img_w, int(anchor_bbox.x_min + max(h_anchor * 18, 475)))

    crop = image[y1:y2, x1:x2]
    if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
        return []

    # Run dedicated dot-matrix OCR
    ocr_boxes = run_dot_matrix_ocr(
        image_crop=crop,
        parent_offset=(float(x1), float(y1)),
        expected_field="mrp",
        engine_mgr=engine_mgr,
    )

    reocr_candidates: List[FieldCandidate] = []
    for ob in ocr_boxes:
        cands = extract_price_candidates_from_text(
            text=ob.text,
            ref_bbox=ob.bbox,
            source="reocr",
            anchor_text="MRP",
            anchor_bbox=anchor_bbox,
            ocr_confidence=ob.confidence,
        )
        reocr_candidates.extend(cands)

    return reocr_candidates


def extract_mrp_reliably(
    token_store: OCRTokenStore,
    image: Optional[np.ndarray] = None,
    engine_mgr: Any = None,
    layout_candidate: Optional[FieldCandidate] = None,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Execute full evidence-driven MRP extraction pipeline:
    1. Incorporate layout-assigned candidate if available
    2. Detect anchors ('MRP', 'M.R.P.', '₹', 'Rs.')
    3. Generate candidates from local spatial neighborhood
    4. Score candidates with positive features and negative classifiers
    5. Trigger targeted re-OCR if ambiguous or faint
    6. Arbitrate best candidate via Decision Engine
    """
    anchors = find_mrp_anchors(token_store)
    candidates: List[FieldCandidate] = []

    # Priority candidate from layout engine
    if layout_candidate:
        candidates.append(layout_candidate)

    # -------------------------------------------------------------
    # Step 1: Anchor-based Local Candidate Search
    # -------------------------------------------------------------
    for anchor_token, anchor_type in anchors:
        # Case A: Same line co-occurrence
        if anchor_token.token_type == "line":
            line_cands = extract_price_candidates_from_text(
                text=anchor_token.text,
                ref_bbox=anchor_token.bbox,
                source="same_line",
                anchor_text=anchor_token.text,
                anchor_bbox=anchor_token.bbox,
                ocr_confidence=anchor_token.ocr_confidence,
                child_tokens=anchor_token.child_tokens,
            )
            candidates.extend(line_cands)

        # Case B: Spatial neighborhood query (right of anchor)
        max_h = max(anchor_token.bbox.height, 20.0) * config.SPATIAL_HORIZONTAL_MAX_RATIO
        right_tokens = token_store.find_tokens_right_of(anchor_token.bbox, max_h_distance=max_h)
        for dist, r_token in right_tokens[:6]:
            r_cands = extract_price_candidates_from_text(
                text=r_token.text,
                ref_bbox=r_token.bbox,
                source="right_adjacent",
                anchor_text=anchor_token.text,
                anchor_bbox=anchor_token.bbox,
                ocr_confidence=r_token.ocr_confidence,
                child_tokens=r_token.child_tokens,
            )
            candidates.extend(r_cands)

        # Case C: Spatial neighborhood query (below anchor)
        max_v = max(anchor_token.bbox.height, 20.0) * config.SPATIAL_VERTICAL_MAX_RATIO
        below_tokens = token_store.find_tokens_below(anchor_token.bbox, max_v_distance=max_v)
        for dist, b_token in below_tokens[:6]:
            b_cands = extract_price_candidates_from_text(
                text=b_token.text,
                ref_bbox=b_token.bbox,
                source="below_adjacent",
                anchor_text=anchor_token.text,
                anchor_bbox=anchor_token.bbox,
                ocr_confidence=b_token.ocr_confidence,
                child_tokens=b_token.child_tokens,
            )
            candidates.extend(b_cands)

        # Case E: Spatial neighborhood query (above anchor, for tabular/stamp layouts)
        above_tokens = token_store.find_tokens_above(anchor_token.bbox, max_v_distance=max_v)
        for dist, ab_token in above_tokens[:6]:
            ab_cands = extract_price_candidates_from_text(
                text=ab_token.text,
                ref_bbox=ab_token.bbox,
                source="above_adjacent",
                anchor_text=anchor_token.text,
                anchor_bbox=anchor_token.bbox,
                ocr_confidence=ab_token.ocr_confidence,
                child_tokens=ab_token.child_tokens,
            )
            candidates.extend(ab_cands)

        # Case D: Right-column table neighborhood (within horizontal distance and +/- 2.5x anchor height)
        for wt in token_store.word_tokens:
            if wt.bbox.x_min >= anchor_token.bbox.x_min and (wt.bbox.x_min - anchor_token.bbox.x_max) <= max_h:
                v_offset = abs(wt.bbox.center_y - anchor_token.bbox.center_y)
                if v_offset <= max(anchor_token.bbox.height, 20.0) * 2.5:
                    col_cands = extract_price_candidates_from_text(
                        text=wt.text,
                        ref_bbox=wt.bbox,
                        source="right_adjacent",
                        anchor_text=anchor_token.text,
                        anchor_bbox=anchor_token.bbox,
                        ocr_confidence=wt.ocr_confidence,
                    )
                    candidates.extend(col_cands)

    # -------------------------------------------------------------
    # Step 2: Global Fallback (only if no anchor candidates found)
    # -------------------------------------------------------------
    if not candidates:
        for line in token_store.line_tokens:
            g_cands = extract_price_candidates_from_text(
                text=line.text,
                ref_bbox=line.bbox,
                source="global_fallback",
                ocr_confidence=line.ocr_confidence,
                child_tokens=line.child_tokens,
            )
            candidates.extend(g_cands)

    # Deduplicate candidates by value and source
    unique_candidates: List[FieldCandidate] = []
    seen = set()
    for c in candidates:
        key = (c.value, c.source, round(c.value_bbox.y_min, 0) if c.value_bbox else 0)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    # -------------------------------------------------------------
    # Step 3: Score all candidates
    # -------------------------------------------------------------
    for c in unique_candidates:
        score_mrp_candidate(c, token_store.image_shape, token_store)

    # Sort candidates
    unique_candidates.sort(key=lambda c: c.field_score, reverse=True)

    # -------------------------------------------------------------
    # Step 4: Targeted Re-OCR if ambiguous or best candidate < threshold
    # -------------------------------------------------------------
    top_score = unique_candidates[0].field_score if unique_candidates else 0.0
    has_strong_candidate = False
    if unique_candidates:
        c0 = unique_candidates[0]
        is_two_decimal = ('.' in c0.value and len(c0.value.split('.')[1]) == 2)
        if c0.field_score >= 80.0 and c0.ocr_confidence >= 0.50 and is_two_decimal:
            has_strong_candidate = True

    needs_reocr = (
        config.TARGETED_REOCR_ENABLED
        and image is not None
        and engine_mgr is not None
        and anchors
        and not has_strong_candidate
    )

    if needs_reocr:
        # Re-OCR around the best explicit anchor
        best_anchor = next((a[0] for a in anchors if a[1] == "explicit"), anchors[0][0])
        re_cands = targeted_mrp_reocr(image, best_anchor.bbox, engine_mgr)
        for rc in re_cands:
            score_mrp_candidate(rc, token_store.image_shape, token_store)
            unique_candidates.append(rc)

        # Re-sort after re-OCR
        unique_candidates.sort(key=lambda c: c.field_score, reverse=True)

    # -------------------------------------------------------------
    # Step 5: Arbitrate via Decision Engine
    # -------------------------------------------------------------
    best_candidate, candidate_summary = arbitrate_candidates(
        field_name="mrp",
        candidates=unique_candidates,
    )

    return best_candidate, candidate_summary
