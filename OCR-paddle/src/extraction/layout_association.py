"""
Layout-Aware Label/Value Association Module.
Performs two-column table and stacked layout analysis on Canonical OCR Tokens:
- Identifies structured multi-row layouts
- Detects label and value columns dynamically
- Clusters tokens into scale-aware horizontal rows
- Groups multi-word labels ('USE BY', 'NET QUANTITY', 'MAX RETAIL PRICE')
- Semantically classifies values (dates, prices, quantities, batches, licenses)
- Constructs a global compatibility score matrix (layout + semantics + OCR)
- Solves global 1-to-1 bipartite assignment to eliminate row-crossing and nearest-neighbour errors
- Computes independent layout_confidence metric
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Set
import re
import numpy as np

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
    looks_like_barcode,
)
from src.utils.geometry import BoundingBox, calculate_iou, distance_between


# -------------------------------------------------------------------------
# Known Field Label Vocabulary & Multi-Word Definitions
# -------------------------------------------------------------------------
MULTI_WORD_ANCHORS: List[Tuple[str, List[str]]] = [
    ("expiry_date", ["use", "by"]),
    ("expiry_date", ["best", "before"]),
    ("expiry_date", ["exp", "date"]),
    ("expiry_date", ["expiry", "date"]),
    ("manufacturing_date", ["mfg", "date"]),
    ("manufacturing_date", ["mfd", "date"]),
    ("manufacturing_date", ["pkd", "date"]),
    ("manufacturing_date", ["pkg", "date"]),
    ("manufacturing_date", ["packed", "on"]),
    ("manufacturing_date", ["date", "of", "mfg"]),
    ("manufacturing_date", ["date", "of", "pkg"]),
    ("manufacturing_date", ["date", "of", "packaging"]),
    ("manufacturing_date", ["date", "of", "manufacture"]),
    ("net_quantity", ["net", "quantity"]),
    ("net_quantity", ["net", "weight"]),
    ("net_quantity", ["net", "wt"]),
    ("net_quantity", ["net", "vol"]),
    ("net_quantity", ["net", "content"]),
    ("net_quantity", ["net", "contents"]),
    ("net_quantity", ["net", "qty"]),
    ("mrp", ["max", "retail", "price"]),
    ("mrp", ["maximum", "retail", "price"]),
    ("mrp", ["max", "price"]),
    ("mrp", ["retail", "price"]),
    ("mrp", ["incl", "of", "all", "taxes"]),
    ("unit_sale_price", ["unit", "sale", "price"]),
    ("unit_sale_price", ["unit", "price"]),
    ("batch_number", ["batch", "no"]),
    ("batch_number", ["batch", "number"]),
    ("batch_number", ["lot", "no"]),
    ("batch_number", ["lot", "number"]),
    ("batch_number", ["b", "no"]),
    ("license_number", ["lic", "no"]),
    ("license_number", ["licence", "no"]),
    ("license_number", ["license", "no"]),
    ("license_number", ["regd", "office"]),
]

SINGLE_WORD_LABELS: Dict[str, str] = {
    "mfg": "manufacturing_date",
    "mfd": "manufacturing_date",
    "pkd": "manufacturing_date",
    "pkg": "manufacturing_date",
    "packed": "manufacturing_date",
    "exp": "expiry_date",
    "expiry": "expiry_date",
    "mrp": "mrp",
    "m.r.p": "mrp",
    "m.r.p.": "mrp",
    "mrr": "mrp",
    "mbp": "mrp",
    "batch": "batch_number",
    "lot": "batch_number",
    "fssai": "license_number",
    "lic": "license_number",
    "licence": "license_number",
    "license": "license_number",
    "usp": "unit_sale_price",
    "weight": "net_quantity",
    "quantity": "net_quantity",
    "net": "net_quantity",
    "qty": "net_quantity",
}


@dataclass
class LabelEntity:
    field_name: str
    text: str
    tokens: List[CanonicalToken]
    bbox: BoundingBox
    ocr_confidence: float

    @property
    def center_y(self) -> float:
        return self.bbox.center_y

    @property
    def center_x(self) -> float:
        return self.bbox.center_x


@dataclass
class ValueEntity:
    text: str
    token: CanonicalToken
    bbox: BoundingBox
    ocr_confidence: float
    semantic_types: Dict[str, float] = field(default_factory=dict)

    @property
    def center_y(self) -> float:
        return self.bbox.center_y

    @property
    def center_x(self) -> float:
        return self.bbox.center_x


@dataclass
class LayoutRow:
    row_idx: int
    y_min: float
    y_max: float
    center_y: float
    label: Optional[LabelEntity] = None
    values: List[ValueEntity] = field(default_factory=list)


@dataclass
class LayoutStructure:
    is_structured: bool
    layout_confidence: float
    columns: List[Dict[str, Any]]
    rows: List[LayoutRow]
    assigned_pairs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structured_layout": self.is_structured,
            "layout_confidence": round(self.layout_confidence, 2),
            "columns": self.columns,
            "rows": [
                {
                    "row_idx": r.row_idx,
                    "y_range": [round(r.y_min, 1), round(r.y_max, 1)],
                    "label": r.label.text if r.label else None,
                    "values": [v.text for v in r.values],
                }
                for r in self.rows
            ],
            "assigned_pairs": self.assigned_pairs,
        }


# -------------------------------------------------------------------------
# 1. Multi-Word Label Grouping
# -------------------------------------------------------------------------
def group_multi_word_labels(words: List[CanonicalToken]) -> Tuple[List[LabelEntity], List[CanonicalToken]]:
    """
    Reconstruct multi-word labels from word tokens while leaving non-label tokens intact.
    Supports:
    1. Single tokens containing multi-word phrases (e.g. 'USE BY', 'BEST BEFORE', 'NET WT.')
    2. Multi-token phrases clustered horizontally across words on the same line band
    3. Single-word labels with punctuation stripped
    Returns: (label_entities, remaining_unassigned_tokens)
    """
    if not words:
        return [], []

    # Calculate median height to form scale-aware line bands
    all_h = [w.bbox.height for w in words if w.bbox.height > 5]
    median_h = float(np.median(all_h)) if all_h else 25.0

    used_token_ids: Set[int] = set()
    label_entities: List[LabelEntity] = []

    # Normalized phrase definitions: e.g. ("net_quantity", "netwt")
    condensed_anchors: List[Tuple[str, str]] = []
    for field_name, phrase_words in MULTI_WORD_ANCHORS:
        condensed = "".join(re.sub(r'[^a-z0-9]', '', w.lower()) for w in phrase_words)
        condensed_anchors.append((field_name, condensed))

    # 1. First pass: Single tokens that contain full multi-word phrase
    for w in words:
        w_norm = re.sub(r'[^a-z0-9]', '', w.text.lower())
        if not w_norm:
            continue

        matched_field = None
        for field_name, condensed in condensed_anchors:
            if w_norm == condensed:
                matched_field = field_name
                break

        if matched_field:
            label_entities.append(
                LabelEntity(
                    field_name=matched_field,
                    text=w.text,
                    tokens=[w],
                    bbox=w.bbox,
                    ocr_confidence=w.ocr_confidence,
                )
            )
            used_token_ids.add(id(w))

    # 2. Second pass: Group words into scale-aware horizontal lines and match multi-word phrases across tokens
    unused_words = [w for w in words if id(w) not in used_token_ids]
    unused_words_sorted = sorted(unused_words, key=lambda w: w.bbox.center_y)
    line_clusters: List[List[CanonicalToken]] = []
    current_cluster: List[CanonicalToken] = []
    current_cluster_y = 0.0

    line_tol = max(median_h * 0.65, 12.0)
    for w in unused_words_sorted:
        if not current_cluster:
            current_cluster.append(w)
            current_cluster_y = w.bbox.center_y
        else:
            if abs(w.bbox.center_y - current_cluster_y) <= line_tol:
                current_cluster.append(w)
                current_cluster_y = float(np.mean([tok.bbox.center_y for tok in current_cluster]))
            else:
                line_clusters.append(current_cluster)
                current_cluster = [w]
                current_cluster_y = w.bbox.center_y
    if current_cluster:
        line_clusters.append(current_cluster)

    # Within each line cluster, sort left-to-right
    for cluster in line_clusters:
        cluster.sort(key=lambda w: w.bbox.x_min)
        c_len = len(cluster)

        # Check multi-word anchors in cluster
        for field_name, phrase_words in MULTI_WORD_ANCHORS:
            p_len = len(phrase_words)
            p_norm = [re.sub(r'[^a-z0-9]', '', pw.lower()) for pw in phrase_words]

            for i in range(c_len - p_len + 1):
                window = cluster[i : i + p_len]
                if any(id(w) in used_token_ids for w in window):
                    continue

                # Check text match
                match = True
                for j, target_word in enumerate(p_norm):
                    w_norm = re.sub(r'[^a-z0-9]', '', window[j].text.lower())
                    if w_norm != target_word:
                        match = False
                        break

                if match:
                    # Check horizontal gap between words in phrase
                    gap_ok = True
                    for j in range(1, p_len):
                        gap = window[j].bbox.x_min - window[j - 1].bbox.x_max
                        if gap > max(median_h * 3.5, 50.0) or gap < -median_h * 0.5:
                            gap_ok = False
                            break

                    if gap_ok:
                        merged_bbox = BoundingBox(
                            x_min=min(w.bbox.x_min for w in window),
                            y_min=min(w.bbox.y_min for w in window),
                            x_max=max(w.bbox.x_max for w in window),
                            y_max=max(w.bbox.y_max for w in window),
                        )
                        full_text = " ".join(w.text for w in window)
                        avg_conf = float(np.mean([w.ocr_confidence for w in window]))
                        label_entities.append(
                            LabelEntity(
                                field_name=field_name,
                                text=full_text,
                                tokens=window,
                                bbox=merged_bbox,
                                ocr_confidence=avg_conf,
                            )
                        )
                        for w in window:
                            used_token_ids.add(id(w))

    # 3. Third pass: Single-word labels from remaining unused words
    for w in words:
        if id(w) in used_token_ids:
            continue
        w_norm = re.sub(r'[^a-z0-9]', '', w.text.lower())
        if w_norm in SINGLE_WORD_LABELS:
            field_name = SINGLE_WORD_LABELS[w_norm]
            label_entities.append(
                LabelEntity(
                    field_name=field_name,
                    text=w.text,
                    tokens=[w],
                    bbox=w.bbox,
                    ocr_confidence=w.ocr_confidence,
                )
            )
            used_token_ids.add(id(w))

    remaining = [w for w in words if id(w) not in used_token_ids]
    return label_entities, remaining


# -------------------------------------------------------------------------
# 1b. Value Token Merging (Units, Currency, Split Dates)
# -------------------------------------------------------------------------
def merge_split_value_tokens(words: List[CanonicalToken], median_h: float) -> List[CanonicalToken]:
    """
    Merge adjacent split tokens on the same line that belong to the same semantic value
    (e.g. '35' + 'g', '₹' + '22.00', '0.62' + '/g').
    """
    if len(words) < 2:
        return words

    words_sorted = sorted(words, key=lambda w: w.bbox.center_y)
    line_clusters: List[List[CanonicalToken]] = []
    current_cluster: List[CanonicalToken] = []
    current_y = 0.0
    line_tol = max(median_h * 0.6, 12.0)

    for w in words_sorted:
        if not current_cluster:
            current_cluster.append(w)
            current_y = w.bbox.center_y
        else:
            if abs(w.bbox.center_y - current_y) <= line_tol:
                current_cluster.append(w)
                current_y = float(np.mean([t.bbox.center_y for t in current_cluster]))
            else:
                line_clusters.append(current_cluster)
                current_cluster = [w]
                current_y = w.bbox.center_y
    if current_cluster:
        line_clusters.append(current_cluster)

    merged_tokens: List[CanonicalToken] = []
    unit_pattern = re.compile(r'^(?:g|gm|gms|gram|grams|kg|kgs|ml|l|ltr|mg|n|u|pcs?|units?|refill)$', re.I)
    usp_unit_pattern = re.compile(r'^(?:/[a-z]+|per\s*[a-z]+)$', re.I)
    currency_pattern = re.compile(r'^(?:[₹]|rs\.?|inr)$', re.I)

    for cluster in line_clusters:
        cluster.sort(key=lambda w: w.bbox.x_min)
        i = 0
        while i < len(cluster):
            tok = cluster[i]
            if i + 1 < len(cluster):
                next_tok = cluster[i + 1]
                gap = next_tok.bbox.x_min - tok.bbox.x_max
                max_gap = max(median_h * 2.5, 35.0)

                should_merge = False
                # Number + Quantity Unit (e.g. '35' + 'g')
                if re.match(r'^\d+(?:\.\d+)?$', tok.text) and unit_pattern.match(next_tok.text) and 0 <= gap <= max_gap:
                    should_merge = True
                # Number + USP Unit (e.g. '0.62' + '/g')
                elif re.match(r'^\d+(?:\.\d+)?$', tok.text) and usp_unit_pattern.match(next_tok.text) and 0 <= gap <= max_gap:
                    should_merge = True
                # Currency + Number (e.g. '₹' + '22.00')
                elif currency_pattern.match(tok.text) and re.match(r'^\d+(?:\.\d{2})?$', next_tok.text) and 0 <= gap <= max_gap:
                    should_merge = True
                # Split dates (e.g. '21/03/' + '2026')
                elif (tok.text.endswith('/') or tok.text.endswith('-')) and re.match(r'^\d{2,4}$', next_tok.text) and 0 <= gap <= max_gap:
                    should_merge = True

                if should_merge:
                    merged_bbox = BoundingBox(
                        x_min=min(tok.bbox.x_min, next_tok.bbox.x_min),
                        y_min=min(tok.bbox.y_min, next_tok.bbox.y_min),
                        x_max=max(tok.bbox.x_max, next_tok.bbox.x_max),
                        y_max=max(tok.bbox.y_max, next_tok.bbox.y_max),
                    )
                    merged_text = f"{tok.text} {next_tok.text}".strip()
                    merged_tok = CanonicalToken(
                        text=merged_text,
                        normalized_text=merged_text.lower(),
                        bbox=merged_bbox,
                        ocr_confidence=float((tok.ocr_confidence + next_tok.ocr_confidence) / 2.0),
                        engine=tok.engine,
                        token_type="word",
                    )
                    merged_tokens.append(merged_tok)
                    i += 2
                    continue

            merged_tokens.append(tok)
            i += 1

    return merged_tokens


# -------------------------------------------------------------------------
# 2. Semantic Value Classification
# -------------------------------------------------------------------------
def classify_value_token(token: CanonicalToken) -> ValueEntity:
    """Classify token semantically against all recognized compliance field patterns."""
    text = token.text.strip()
    scores: Dict[str, float] = {}

    # Check Date
    is_d, d_val, d_conf = looks_like_date(text)
    if is_d:
        scores["date"] = d_conf

    # Check Price / MRP
    is_mrp = bool(re.search(r'^(?:[₹Rs.]\s*)?\d+(?:\.\d{2})?(?:/-)?$', text))
    if is_mrp and not is_d:
        # Check if 4-digit year
        if text.isdigit() and 2024 <= int(text) <= 2035:
            scores["date"] = 0.8
        else:
            scores["mrp"] = 0.9

    # Check Quantity
    is_q, q_val, q_conf = looks_like_quantity(text)
    if is_q:
        scores["net_quantity"] = q_conf

    # Check USP
    is_usp, usp_val, usp_conf = looks_like_unit_sale_price(text)
    if is_usp:
        scores["unit_sale_price"] = usp_conf

    # Check License (FSSAI or Ayush)
    is_lic, lic_val, lic_conf = looks_like_license(text)
    if is_lic:
        scores["license_number"] = lic_conf

    # Check Batch
    is_b, b_val, b_conf = looks_like_batch(text)
    if is_b and not is_d and not is_mrp and not is_q:
        scores["batch_number"] = b_conf

    return ValueEntity(
        text=text,
        token=token,
        bbox=token.bbox,
        ocr_confidence=token.ocr_confidence,
        semantic_types=scores,
    )


# -------------------------------------------------------------------------
# 3. Dynamic Column & Row Detection
# -------------------------------------------------------------------------
def detect_columns_and_rows(
    labels: List[LabelEntity],
    values: List[ValueEntity],
    image_shape: Tuple[int, int] = (1000, 1000),
) -> Tuple[List[Dict[str, Any]], List[LayoutRow], float]:
    """
    Cluster labels and values into dynamic columns and scale-aware horizontal rows.
    Returns: (columns_info, rows_list, column_confidence)
    """
    if not labels or not values:
        return [], [], 0.0

    # Calculate median text height for scale-aware clustering
    all_heights = [l.bbox.height for l in labels] + [v.bbox.height for v in values]
    median_h = float(np.median(all_heights)) if all_heights else 25.0
    v_tolerance = median_h * config.ROW_VERTICAL_TOLERANCE_MULTIPLIER

    # 1. Column analysis:
    # Labels usually cluster on the left; values usually cluster on the right.
    label_x_centers = [l.center_x for l in labels]
    value_x_centers = [v.center_x for v in values]

    mean_label_x = float(np.mean(label_x_centers))
    mean_value_x = float(np.mean(value_x_centers))

    # Separation check: Value column should generally be to the right of label column
    h_gap = mean_value_x - mean_label_x
    column_confidence = 0.5
    if h_gap > median_h * config.COLUMN_CLUSTER_TOLERANCE_MULTIPLIER:
        # Clear horizontal column separation
        column_confidence = min(0.95, 0.65 + (h_gap / (image_shape[1] * 0.5)))
    elif h_gap > 0:
        column_confidence = 0.60
    else:
        # Stacked or irregular layout
        column_confidence = 0.40

    columns_info = [
        {
            "type": "label",
            "x_range": [
                round(float(min(l.bbox.x_min for l in labels)), 1),
                round(float(max(l.bbox.x_max for l in labels)), 1),
            ],
            "mean_center_x": round(mean_label_x, 1),
        },
        {
            "type": "value",
            "x_range": [
                round(float(min(v.bbox.x_min for v in values)), 1),
                round(float(max(v.bbox.x_max for v in values)), 1),
            ],
            "mean_center_x": round(mean_value_x, 1),
        },
    ]

    # 2. Row clustering:
    # Sort all entities vertically by center_y
    # We cluster tokens that share similar vertical center (within v_tolerance)
    sorted_labels = sorted(labels, key=lambda l: l.center_y)
    rows: List[LayoutRow] = []

    for r_idx, lbl in enumerate(sorted_labels):
        r_ymin = lbl.bbox.y_min
        r_ymax = lbl.bbox.y_max
        r_cy = lbl.center_y

        # Find all values belonging to this row band
        row_values = []
        for val in values:
            v_cy = val.center_y
            v_diff = abs(v_cy - r_cy)
            # Check vertical overlap or close vertical center
            v_overlap = min(r_ymax, val.bbox.y_max) - max(r_ymin, val.bbox.y_min)
            if v_overlap > 0 or v_diff <= v_tolerance:
                row_values.append(val)

        # Sort row values from left to right
        row_values.sort(key=lambda v: v.bbox.x_min)

        row_obj = LayoutRow(
            row_idx=r_idx,
            y_min=r_ymin,
            y_max=r_ymax,
            center_y=r_cy,
            label=lbl,
            values=row_values,
        )
        rows.append(row_obj)

    return columns_info, rows, column_confidence


# -------------------------------------------------------------------------
# 4. Pair Scoring Function
# -------------------------------------------------------------------------
def score_label_value_pair(
    label: LabelEntity,
    value: ValueEntity,
    median_h: float,
    is_in_same_row: bool,
) -> Tuple[float, List[str]]:
    """
    Score a candidate (Label, Value) association using visual layout and semantic compatibility:
    - Same Row: +30
    - Value to the right of label: +20
    - Center alignment: up to +20
    - Reasonable horizontal gap: +15
    - Explicit anchor text match: +30
    - Semantic type compatibility: +30
    - Strong negative penalty for mismatched semantic type: -40
    - Different row penalty: -30
    """
    score = 0.0
    reasons = []

    # 1. Row Alignment
    if is_in_same_row:
        score += 30.0
        reasons.append("same_row (+30)")
    else:
        score -= 30.0
        reasons.append("different_row (-30)")

    # 2. Horizontal Relationship (Value should be right of label)
    if value.bbox.x_min >= label.bbox.x_max - 5.0:
        score += 20.0
        reasons.append("right_of_label (+20)")
    elif value.bbox.x_min >= label.bbox.x_min:
        score += 10.0
        reasons.append("partially_right (+10)")
    else:
        score -= 20.0
        reasons.append("left_of_label (-20)")

    # 3. Vertical Center Alignment
    v_diff = abs(value.center_y - label.center_y)
    max_tol = max(median_h * 1.5, 25.0)
    if v_diff <= max_tol:
        alignment_score = 20.0 * (1.0 - (v_diff / max_tol))
        score += alignment_score
        reasons.append(f"center_alignment (+{alignment_score:.1f})")

    # 4. Horizontal Gap
    h_gap = max(0.0, value.bbox.x_min - label.bbox.x_max)
    if 5.0 <= h_gap <= median_h * 15.0:
        score += 15.0
        reasons.append("reasonable_gap (+15)")
    elif h_gap > median_h * 25.0:
        score -= 15.0
        reasons.append("excessive_gap (-15)")

    # 5. Semantic Compatibility (FATAL CHECKS)
    target_field = label.field_name
    sem_types = value.semantic_types

    # Date fields (MFG & EXP)
    if target_field in {"manufacturing_date", "expiry_date"}:
        if "date" in sem_types:
            score += 35.0
            reasons.append(f"semantic_date_match (+35)")
        elif "mrp" in sem_types:
            # Price assigned to date field -> fatal mismatch penalty
            score -= 90.0
            reasons.append("date_price_mismatch (-90)")
        elif "net_quantity" in sem_types:
            score -= 75.0
            reasons.append("date_quantity_mismatch (-75)")

    # MRP / Price field
    elif target_field == "mrp":
        if "mrp" in sem_types:
            score += 35.0
            reasons.append("semantic_price_match (+35)")
        elif "date" in sem_types:
            # Date assigned to MRP -> fatal mismatch penalty
            score -= 90.0
            reasons.append("mrp_date_mismatch (-90)")
        elif "net_quantity" in sem_types:
            score -= 75.0
            reasons.append("mrp_quantity_mismatch (-75)")

    # Net Quantity field
    elif target_field == "net_quantity":
        if "net_quantity" in sem_types:
            score += 35.0
            reasons.append("semantic_quantity_match (+35)")
        elif "date" in sem_types:
            score -= 80.0
            reasons.append("quantity_date_mismatch (-80)")

    # Batch Number field
    elif target_field == "batch_number":
        if "batch_number" in sem_types or (not sem_types.get("date") and not sem_types.get("mrp")):
            score += 25.0
            reasons.append("semantic_batch_match (+25)")
        elif "date" in sem_types:
            score -= 75.0
            reasons.append("batch_date_mismatch (-75)")

    # License Number field
    elif target_field == "license_number":
        if "license_number" in sem_types:
            score += 35.0
            reasons.append("semantic_license_match (+35)")
        elif "date" in sem_types:
            score -= 75.0
            reasons.append("license_date_mismatch (-75)")

    # Unit Sale Price field
    elif target_field == "unit_sale_price":
        if "unit_sale_price" in sem_types:
            score += 35.0
            reasons.append("semantic_usp_match (+35)")

    return score, reasons


# -------------------------------------------------------------------------
# 5. Global Assignment Solver
# -------------------------------------------------------------------------
def solve_global_assignment(
    labels: List[LabelEntity],
    values: List[ValueEntity],
    median_h: float,
    rows: List[LayoutRow],
) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[LabelEntity, ValueEntity, float, float]]]:
    """
    Construct candidate score matrix and solve 1-to-1 bipartite assignment globally.
    Returns:
    - assigned_pairs_metadata: List of assignment dicts for JSON audit
    - field_to_assignment: Dict mapping field_name -> (label, value, pair_score, layout_confidence)
    """
    if not labels or not values:
        return [], {}

    # Build row lookup by object id to avoid unhashable dataclass issues
    label_to_row = {id(r.label): r for r in rows if r.label}

    # Score matrix of size [num_labels, num_values]
    n_lbl = len(labels)
    n_val = len(values)
    score_matrix = np.zeros((n_lbl, n_val), dtype=float)
    reasons_matrix: List[List[List[str]]] = [[[] for _ in range(n_val)] for _ in range(n_lbl)]

    for i, lbl in enumerate(labels):
        row_obj = label_to_row.get(id(lbl))
        row_value_ids = set(id(v) for v in row_obj.values) if row_obj else set()

        for j, val in enumerate(values):
            is_same_row = id(val) in row_value_ids
            s, r = score_label_value_pair(lbl, val, median_h, is_same_row)
            score_matrix[i, j] = s
            reasons_matrix[i][j] = r

    # Solve bipartite assignment with uniqueness constraint
    # We greedily assign highest score pairs, ensuring 1-to-1 matching (no value reuse)
    assigned_labels: Set[int] = set()
    assigned_values: Set[int] = set()

    # Flatten entries: (score, i, j) sorted descending
    candidates = []
    for i in range(n_lbl):
        for j in range(n_val):
            candidates.append((score_matrix[i, j], i, j))
    candidates.sort(key=lambda x: x[0], reverse=True)

    assigned_pairs: List[Dict[str, Any]] = []
    field_to_assignment: Dict[str, Tuple[LabelEntity, ValueEntity, float, float]] = {}

    for score, i, j in candidates:
        if i in assigned_labels or j in assigned_values:
            continue
        # Minimum threshold to accept an assignment
        if score < 15.0:
            continue

        lbl = labels[i]
        val = values[j]

        # Calculate layout confidence based on score margin over second-best value for this label
        row_scores = sorted([score_matrix[i, k] for k in range(n_val) if k != j], reverse=True)
        second_best = row_scores[0] if row_scores else 0.0
        margin = score - second_best

        # Layout confidence scaled between 0.50 and 0.98
        layout_conf = float(np.clip(0.60 + (margin / 60.0), 0.50, 0.98))

        assigned_labels.add(i)
        assigned_values.add(j)

        pair_dict = {
            "label": lbl.text,
            "field": lbl.field_name,
            "value": val.text,
            "score": round(score, 1),
            "layout_confidence": round(layout_conf, 2),
            "margin": round(margin, 1),
            "label_bbox": lbl.bbox.to_dict(),
            "value_bbox": val.bbox.to_dict(),
            "reasons": reasons_matrix[i][j],
            "status": "verified" if margin >= config.LAYOUT_ASSIGNMENT_AMBIGUITY_MARGIN else "needs_recheck",
        }
        assigned_pairs.append(pair_dict)
        field_to_assignment[lbl.field_name] = (lbl, val, score, layout_conf)

    return assigned_pairs, field_to_assignment


# -------------------------------------------------------------------------
# 6. Top-Level Layout Association Pipeline
# -------------------------------------------------------------------------
def analyze_label_layout(
    token_store: OCRTokenStore,
) -> Tuple[LayoutStructure, Dict[str, Tuple[LabelEntity, ValueEntity, float, float]]]:
    """
    Execute full layout-aware analysis:
    1. Reconstruct multi-word labels from canonical tokens
    2. Semantically classify value tokens
    3. Detect column and row structure
    4. Solve global 1-to-1 bipartite assignment
    5. Return LayoutStructure and field assignment mapping
    """
    words = token_store.word_tokens
    if len(words) < 2:
        return LayoutStructure(False, 0.0, [], []), {}

    # Step 1: Reconstruct labels and remaining value tokens
    labels, remaining_words = group_multi_word_labels(words)
    if not labels or len(remaining_words) < 1:
        return LayoutStructure(False, 0.0, [], []), {}

    # Step 2: Classify remaining words as semantic value entities
    all_heights = [w.bbox.height for w in words if w.bbox.height > 5]
    median_h = float(np.median(all_heights)) if all_heights else 25.0
    merged_remaining = merge_split_value_tokens(remaining_words, median_h)
    values = [classify_value_token(w) for w in merged_remaining]

    # Step 3: Column and row clustering
    cols, rows, col_conf = detect_columns_and_rows(labels, values, token_store.image_shape)

    # Determine structured layout boolean
    has_min_rows = len(rows) >= config.LAYOUT_MIN_ROWS
    is_structured = has_min_rows and (col_conf >= config.LAYOUT_MIN_COLUMN_CONFIDENCE or len(labels) >= 3)
    layout_confidence = float(np.clip((col_conf * 0.5) + (min(len(rows), 5) * 0.1), 0.4, 0.95))

    # Step 4: Solve global assignment
    all_heights = [l.bbox.height for l in labels] + [v.bbox.height for v in values]
    median_h = float(np.median(all_heights)) if all_heights else 25.0

    assigned_pairs, field_assignments = solve_global_assignment(labels, values, median_h, rows)

    layout_struct = LayoutStructure(
        is_structured=is_structured,
        layout_confidence=layout_confidence,
        columns=cols,
        rows=rows,
        assigned_pairs=assigned_pairs,
    )

    return layout_struct, field_assignments
