"""
2D Spatial Key-Value Matcher.
Associates semantic label keys with corresponding values using 2D geometric rays (rightward and downward).
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any, Callable
from src.ocr.engine_manager import OCRBox
from src.utils.geometry import BoundingBox, is_horizontally_aligned, is_vertically_aligned, distance_between
from src.extraction import patterns


@dataclass
class KeyMatch:
    field_name: str
    key_box: OCRBox
    value_text: str
    value_box: Optional[OCRBox]
    ocr_confidence: float
    pattern_confidence: float
    spatial_score: float
    combined_confidence: float
    match_source: str  # 'same_line', 'right_adjacent', 'below_adjacent', 'global_fallback'


# Semantic regexes to locate label keys on packaging
KEY_DEFINITIONS: Dict[str, List[re.Pattern]] = {
    "net_quantity": [
        re.compile(r'\bnet\s*(?:quantity|weight|wt|vol|content)?\b', re.IGNORECASE),
        re.compile(r'\bnet\s*wt\.?\b', re.IGNORECASE),
        re.compile(r'\bweight\b', re.IGNORECASE),
    ],
    "mrp": [
        re.compile(r'\bm\.?r\.?p\.?\b', re.IGNORECASE),
        re.compile(r'\bmax(?:imum)?\s*retail\s*price\b', re.IGNORECASE),
    ],
    "unit_sale_price": [
        re.compile(r'\bunit\s*sale\s*price\b', re.IGNORECASE),
        re.compile(r'\busp\b', re.IGNORECASE),
    ],
    "manufacturing_date": [
        re.compile(r'\bmfg(?:\.|\s*date)?\b', re.IGNORECASE),
        re.compile(r'\bpacked\s*(?:on|date)?\b', re.IGNORECASE),
        re.compile(r'\bpkd(?:\.|\s*date)?\b', re.IGNORECASE),
        re.compile(r'\bdate\s*of\s*(?:mfg|packaging|packing)\b', re.IGNORECASE),
    ],
    "expiry_date": [
        re.compile(r'\bexp(?:\.|\s*date)?\b', re.IGNORECASE),
        re.compile(r'\buse\s*by\b', re.IGNORECASE),
        re.compile(r'\bbest\s*before\b', re.IGNORECASE),
        re.compile(r'\bexpiry\s*(?:date)?\b', re.IGNORECASE),
    ],
    "batch_number": [
        re.compile(r'\bbatch(?:\s*no\.?)?\b', re.IGNORECASE),
        re.compile(r'\blot(?:\s*no\.?)?\b', re.IGNORECASE),
        re.compile(r'\bb\.?\s*no\.?\b', re.IGNORECASE),
        re.compile(r'\bmachine\s*code\b', re.IGNORECASE),
    ],
    "license_number": [
        re.compile(r'\bfssai\b', re.IGNORECASE),
        re.compile(r'\blic(?:\.|\s*no\.?)?\b', re.IGNORECASE),
        re.compile(r'\bregn(?:\.|\s*no\.?)?\b', re.IGNORECASE),
    ],
}

# Value extractors mapping
FIELD_EXTRACTORS: Dict[str, Callable[[str], Optional[Tuple[str, float]]]] = {
    "net_quantity": patterns.extract_net_quantity,
    "mrp": patterns.extract_mrp,
    "unit_sale_price": patterns.extract_unit_sale_price,
    "manufacturing_date": patterns.extract_date,
    "expiry_date": patterns.extract_date,
    "batch_number": patterns.extract_batch_number,
    "license_number": patterns.extract_license_number,
}


def find_key_boxes(lines: List[OCRBox], words: List[OCRBox], field_name: str) -> List[OCRBox]:
    """Find all OCR boxes (lines or words) matching the key definition for a given field."""
    regex_list = KEY_DEFINITIONS.get(field_name, [])
    matching_boxes = []

    # Check words and lines
    for box in words + lines:
        for reg in regex_list:
            if reg.search(box.text):
                matching_boxes.append(box)
                break
    return matching_boxes


def match_field_spatially(
    field_name: str,
    lines: List[OCRBox],
    words: List[OCRBox],
    exclude_values: Optional[List[str]] = None,
) -> Optional[KeyMatch]:
    """
    Perform 2D spatial matching for a specific field:
    1. Check if key and value reside on the same line box.
    2. Raycast rightward to find value horizontally aligned with key.
    3. Raycast downward to find value vertically aligned below key.
    4. Fallback to global pattern search across all text.
    """
    extractor = FIELD_EXTRACTORS.get(field_name)
    if not extractor:
        return None

    exclude_set = set(exclude_values or [])
    key_regexes = KEY_DEFINITIONS.get(field_name, [])

    # Strategy 1: Same-line co-occurrence in merged line phrases
    for line in lines:
        for reg in key_regexes:
            if reg.search(line.text):
                # Test if line also contains the extracted value
                extracted = extractor(line.text)
                if extracted and extracted[0] not in exclude_set:
                    val, pat_conf = extracted
                    comb_conf = (line.confidence * 0.4) + (pat_conf * 0.4) + 0.2
                    return KeyMatch(
                        field_name=field_name,
                        key_box=line,
                        value_text=val,
                        value_box=line,
                        ocr_confidence=line.confidence,
                        pattern_confidence=pat_conf,
                        spatial_score=1.0,
                        combined_confidence=comb_conf,
                        match_source="same_line",
                    )

    # Find candidate key boxes
    key_boxes = find_key_boxes(lines, words, field_name)

    # Strategy 2 & 3: 2D Spatial Raycasting from detected key boxes
    best_candidate: Optional[KeyMatch] = None

    for k_box in key_boxes:
        # Search all words/lines located near k_box
        candidates = []
        for candidate_box in words + lines:
            if candidate_box is k_box:
                continue

            # Candidate to the right (same line)
            is_right = (
                candidate_box.bbox.x_min >= k_box.bbox.x_min
                and is_horizontally_aligned(k_box.bbox, candidate_box.bbox, max_v_overlap_ratio=0.7)
            )

            # Candidate below (same column)
            is_below = (
                candidate_box.bbox.y_min >= k_box.bbox.y_min
                and is_vertically_aligned(k_box.bbox, candidate_box.bbox, max_h_overlap_ratio=0.8)
            )

            if is_right or is_below:
                dist = distance_between(k_box.bbox, candidate_box.bbox)
                source = "right_adjacent" if is_right else "below_adjacent"
                candidates.append((dist, candidate_box, source))

        # Sort candidates by spatial distance
        candidates.sort(key=lambda x: x[0])

        for dist, c_box, source in candidates[:8]:
            extracted = extractor(c_box.text)
            if extracted and extracted[0] not in exclude_set:
                val, pat_conf = extracted
                # Spatial score degrades with Euclidean distance relative to key height
                max_dist = max(k_box.bbox.height, 20.0) * 12.0
                spatial_score = max(0.2, 1.0 - (dist / max_dist))
                comb_conf = (c_box.confidence * 0.4) + (pat_conf * 0.4) + (spatial_score * 0.2)

                cand_match = KeyMatch(
                    field_name=field_name,
                    key_box=k_box,
                    value_text=val,
                    value_box=c_box,
                    ocr_confidence=c_box.confidence,
                    pattern_confidence=pat_conf,
                    spatial_score=spatial_score,
                    combined_confidence=comb_conf,
                    match_source=source,
                )

                if best_candidate is None or comb_conf > best_candidate.combined_confidence:
                    best_candidate = cand_match

    if best_candidate:
        return best_candidate

    # Strategy 4: Global fallback pattern scan across all detected lines
    for line in lines:
        extracted = extractor(line.text)
        if extracted and extracted[0] not in exclude_set:
            val, pat_conf = extracted
            # Penalize slightly because there was no adjacent key
            comb_conf = (line.confidence * 0.4) + (pat_conf * 0.4)
            cand_match = KeyMatch(
                field_name=field_name,
                key_box=line,
                value_text=val,
                value_box=line,
                ocr_confidence=line.confidence,
                pattern_confidence=pat_conf,
                spatial_score=0.4,
                combined_confidence=comb_conf,
                match_source="global_fallback",
            )
            if best_candidate is None or comb_conf > best_candidate.combined_confidence:
                best_candidate = cand_match

    return best_candidate
