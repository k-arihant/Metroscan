"""
Dot-Matrix and Dot-Stamped Text Recognition Module.
Detects dot-matrix regions via connected component and stroke discontinuity analysis,
generates multiple morphological and contrast enhancement variants,
runs field-aware PaddleOCR with post-hoc character set filtering,
performs character-level consensus voting, and preserves exact image-space coordinates.

Migration note: EasyOCR and Tesseract have been replaced with PaddleOCR.
PSM-mode selection (select_psm_for_crop) has been removed as it is Tesseract-specific.
Allowlist semantics are preserved via post-processing in OCREngineManager.run_paddle().
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Set
import re
import cv2
import numpy as np

import config
from src.ocr.engine_manager import OCRBox, OCREngineManager
from src.utils.geometry import BoundingBox


@dataclass
class DotMatrixReport:
    is_dot_matrix: bool
    confidence: float
    component_count: int
    dot_density: float
    regularity_score: float
    discontinuity_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_dot_matrix": self.is_dot_matrix,
            "confidence": round(self.confidence, 3),
            "component_count": self.component_count,
            "dot_density": round(self.dot_density, 3),
            "regularity_score": round(self.regularity_score, 3),
            "discontinuity_score": round(self.discontinuity_score, 3),
        }


def detect_dot_matrix_region(image_crop: np.ndarray) -> DotMatrixReport:
    """
    Determine if an image region exhibits characteristics of dot-matrix / inkjet printing:
    - High count of small disjoint blobs with area 3 to 120 pixels
    - High aspect ratio regularity (circular or small square blobs, aspect ratio 0.5 to 2.0)
    - Low stroke continuity (many disconnected components relative to total dark area)
    - Regular spacing / pitch between components (monospaced grid evidence)
    """
    if image_crop is None or image_crop.size == 0:
        return DotMatrixReport(False, 0.0, 0, 0.0, 0.0, 0.0)

    # Convert to grayscale
    if len(image_crop.shape) == 3:
        gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_crop.copy()

    h, w = gray.shape[:2]
    total_pixels = h * w
    if total_pixels < 100:
        return DotMatrixReport(False, 0.0, 0, 0.0, 0.0, 0.0)

    # Otsu binarization to separate text dots from background
    # Check if text is dark on light or light on dark
    mean_val = np.mean(gray)
    if mean_val < 127:
        # Light text on dark background -> invert
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # Dark text on light background -> invert so foreground dots are 255
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Connected component analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    if num_labels <= 1:
        return DotMatrixReport(False, 0.0, 0, 0.0, 0.0, 0.0)

    # Filter background component (index 0)
    stats = stats[1:]
    centroids = centroids[1:]

    # A dot in inkjet/dot-matrix printing typically has:
    # area between 2 and 150 px (depending on resolution)
    # width and height between 1 and 20 px
    dot_candidates = []
    x_positions = []
    y_positions = []
    total_fg_area = 0

    for stat, cent in zip(stats, centroids):
        area = stat[cv2.CC_STAT_AREA]
        cw = stat[cv2.CC_STAT_WIDTH]
        ch = stat[cv2.CC_STAT_HEIGHT]
        total_fg_area += area

        if 2 <= area <= 180 and 1 <= cw <= 25 and 1 <= ch <= 25:
            aspect = float(cw) / float(ch) if ch > 0 else 1.0
            if 0.35 <= aspect <= 2.8:
                dot_candidates.append(stat)
                x_positions.append(cent[0])
                y_positions.append(cent[1])

    num_dots = len(dot_candidates)
    if total_fg_area == 0:
        return DotMatrixReport(False, 0.0, 0, 0.0, 0.0, 0.0)

    dot_fg_ratio = sum(s[cv2.CC_STAT_AREA] for s in dot_candidates) / float(total_fg_area)

    # Stroke discontinuity: high number of disconnected components per unit area
    dot_density = (num_dots / float(total_pixels)) * 1000.0  # dots per 1000 px

    # Regularity of spacing: standard deviation of horizontal gaps between sorted dot centroids
    regularity_score = 0.5
    if len(x_positions) >= 6:
        x_sorted = np.sort(x_positions)
        diffs = np.diff(x_sorted)
        # Filter 0 or extreme diffs
        valid_diffs = diffs[(diffs > 1.0) & (diffs < 40.0)]
        if len(valid_diffs) >= 4:
            std_diff = float(np.std(valid_diffs))
            mean_diff = float(np.mean(valid_diffs))
            cv_diff = (std_diff / mean_diff) if mean_diff > 0 else 1.0
            # Lower coefficient of variation means more regular pitch
            regularity_score = float(np.clip(1.0 - (cv_diff * 0.5), 0.1, 1.0))

    # Discontinuity score
    discontinuity_score = float(np.clip(dot_fg_ratio * 1.2, 0.0, 1.0))

    # Overall dot-matrix confidence
    # Requires reasonable count of small dots, pitch regularity, and disconnected components
    score = 0.0
    if num_dots >= 8 and dot_density >= 0.30:
        score += 0.30
    if num_dots >= 25:
        score += 0.25
    if num_dots >= 50:
        score += 0.15
    if dot_fg_ratio >= 0.10:
        score += 0.15
    if regularity_score >= 0.50:
        score += 0.15

    confidence = float(np.clip(score, 0.0, 0.99))
    is_dot_matrix = confidence >= 0.50

    return DotMatrixReport(
        is_dot_matrix=is_dot_matrix,
        confidence=confidence,
        component_count=num_dots,
        dot_density=dot_density,
        regularity_score=regularity_score,
        discontinuity_score=discontinuity_score,
    )


def generate_dot_matrix_variants(
    crop: np.ndarray,
    scale_factors: Optional[List[float]] = None,
    kernel_sizes: Optional[List[Tuple[int, int]]] = None,
) -> List[Tuple[str, np.ndarray, float]]:
    """
    Generate multiple specialized preprocessing variants for dot-matrix text:
    - Variant A: Grayscale + 2x/3x/4x upscale with bicubic interpolation
    - Variant B: Grayscale + CLAHE for low-contrast stamps + upscale
    - Variant C: Adaptive Gaussian thresholding + upscale
    - Variant D: Light Gaussian blur + morphological closing (to bridge dots) + upscale
    - Variant E: Directional dot bridging with small kernel sizes
    Returns: List of (variant_name, processed_image, scale_factor)
    """
    if crop is None or crop.size == 0:
        return []

    scales = scale_factors or config.DOT_MATRIX_UPSCALE_FACTORS
    kernels = kernel_sizes or config.DOT_MATRIX_KERNEL_SIZES

    if len(crop.shape) == 3:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop.copy()

    h, w = gray.shape[:2]
    variants: List[Tuple[str, np.ndarray, float]] = []

    # Choose primary scale factor (3.0 default for high OCR fidelity)
    primary_scale = scales[1] if len(scales) > 1 else 3.0

    # 1. Variant A: Grayscale + Bilateral Filter + Upscale
    denoised = cv2.bilateralFilter(gray, d=5, sigmaColor=40, sigmaSpace=40)
    up_a = cv2.resize(denoised, (int(w * primary_scale), int(h * primary_scale)), interpolation=cv2.INTER_CUBIC)
    variants.append(("dot_matrix_upscale", up_a, primary_scale))

    # 2. Variant B: Upscale + CLAHE
    if config.DOT_MATRIX_CLAHE_ENABLED:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        up_b = cv2.resize(clahe_img, (int(w * primary_scale), int(h * primary_scale)), interpolation=cv2.INTER_CUBIC)
        variants.append(("dot_matrix_clahe", up_b, primary_scale))

    # 3. Variant C: Adaptive Gaussian Thresholding + Upscale
    if config.DOT_MATRIX_ADAPTIVE_THRESHOLD_ENABLED:
        # Check polarity
        mean_b = np.mean(gray)
        if mean_b < 127:
            th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        else:
            th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 4)
        up_c = cv2.resize(th, (int(w * primary_scale), int(h * primary_scale)), interpolation=cv2.INTER_NEAREST)
        variants.append(("dot_matrix_thresh", up_c, primary_scale))

    # 4. Variant D: Light Gaussian Blur + Morphological Closing
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    for k_size in kernels:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, k_size)
        # Determine closing on dark text
        if np.mean(blurred) > 127:
            # Dark dots on light background: erode or black-hat / inverse close
            inv = 255 - blurred
            closed_inv = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, kernel)
            bridged = 255 - closed_inv
        else:
            bridged = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

        up_d = cv2.resize(bridged, (int(w * primary_scale), int(h * primary_scale)), interpolation=cv2.INTER_CUBIC)
        variants.append((f"dot_matrix_bridge_{k_size[0]}x{k_size[1]}", up_d, primary_scale))

    return variants



def normalize_confusable_characters(text: str, field_type: str) -> str:
    """
    Controlled character confusion normalization based on expected field semantics:
    - Dates: O -> 0, I -> 1, l -> 1, S -> 5, B -> 8, G -> 6 (when surrounded by digits/slashes)
    - MRP: O -> 0, S -> 5, B -> 8, G -> 6 (when adjacent to digits or decimal)
    - Batch: DO NOT globally replace letters; preserve alphanumeric identity unless obvious OCR noise
    """
    if not text:
        return text

    if field_type in {"date", "manufacturing_date", "expiry_date"}:
        # In a date context, letters between digits or slashes are almost certainly numbers
        res = text
        # Date patterns e.g. 06/O9/26 -> 06/09/26
        res = re.sub(r'(?<=\d)[Oo](?=\d|[/.-]|$)', '0', res)
        res = re.sub(r'(?<=[/.-])[Oo](?=\d)', '0', res)
        res = re.sub(r'\b[Oo](?=\d)', '0', res)
        res = re.sub(r'(?<=\d)[Oo]\b', '0', res)
        res = re.sub(r'(?<=\d)[Il|](?=\d)', '1', res)
        res = re.sub(r'(?<=[/.-])[Il|](?=\d)', '1', res)
        res = re.sub(r'(?<=\d)[Gg](?=[/.-]|\d|$)', '6', res)
        res = re.sub(r'(?<=[/.-])[Gg](?=\d)', '6', res)
        res = re.sub(r'(?<=\d)[Ss](?=[/.-]|\d|$)', '5', res)
        res = re.sub(r'(?<=[/.-])[Ss](?=\d)', '5', res)
        res = re.sub(r'(?<=\d)[Bb](?=[/.-]|\d|$)', '8', res)
        return res

    elif field_type in {"mrp", "price", "unit_sale_price"}:
        res = text
        # Decimal numbers e.g. 22 OO -> 22.00, 22.OO -> 22.00, 36O.00 -> 360.00
        res = re.sub(r'(?<=\d)\s+[Oo]{2}\b', '.00', res)
        res = re.sub(r'[Oo]{2}\b', '00', res)
        res = re.sub(r'(?<=\d)[Oo](?=\d|\.|$)', '0', res)
        res = re.sub(r'(?<=\.)[Oo](?=\d|$)', '0', res)
        res = re.sub(r'(?<=\d)[Il|](?=\d)', '1', res)
        res = re.sub(r'(?<=\d)[Ss](?=\d)', '5', res)
        res = re.sub(r'(?<=\d)[Gg](?=\d)', '6', res)
        return res

    elif field_type in {"net_quantity", "quantity"}:
        res = text
        # Number before unit e.g. 5OO g -> 500 g
        res = re.sub(r'(?<=\d)[Oo]+(?=\s*[a-zA-Z])', '0', res)
        res = re.sub(r'\b[Oo](?=\d+\s*[a-zA-Z])', '0', res)
        return res

    return text


def character_consensus_voting(
    candidate_strings: List[Tuple[str, float]],
    field_type: str = "alphanumeric",
) -> Tuple[str, float, float]:
    """
    Perform multi-variant character-level positional consensus voting across variant OCR outputs.
    Returns: (consensus_text, ocr_confidence, consensus_score)
    """
    if not candidate_strings:
        return "", 0.0, 0.0

    # Clean strings
    cleaned = []
    for s, conf in candidate_strings:
        s_norm = normalize_confusable_characters(s.strip(), field_type)
        if s_norm:
            cleaned.append((s_norm, conf))

    if not cleaned:
        return "", 0.0, 0.0

    if len(cleaned) == 1:
        return cleaned[0][0], cleaned[0][1], 1.0

    # 1. Exact string matches (full string consensus)
    text_counts: Dict[str, float] = {}
    for s, conf in cleaned:
        text_counts[s] = text_counts.get(s, 0.0) + conf + 1.0

    best_text = max(text_counts.items(), key=lambda x: x[1])[0]
    match_ratio = sum(1 for s, _ in cleaned if s == best_text) / float(len(cleaned))

    # If full match agreement is high, return it
    if match_ratio >= 0.5:
        avg_conf = float(np.mean([conf for s, conf in cleaned if s == best_text]))
        return best_text, avg_conf, float(match_ratio)

    # 2. Positional character-level voting for strings of identical length
    lengths = [len(s) for s, _ in cleaned]
    mode_len = max(set(lengths), key=lengths.count)

    same_len_strings = [(s, conf) for s, conf in cleaned if len(s) == mode_len]
    if len(same_len_strings) >= 2:
        consensus_chars = []
        total_votes_agreement = 0.0
        for pos in range(mode_len):
            char_votes: Dict[str, float] = {}
            for s, conf in same_len_strings:
                ch = s[pos]
                char_votes[ch] = char_votes.get(ch, 0.0) + conf
            best_char, best_vote = max(char_votes.items(), key=lambda x: x[1])
            consensus_chars.append(best_char)
            total_votes_agreement += best_vote / sum(char_votes.values())

        consensus_str = "".join(consensus_chars)
        avg_char_agreement = total_votes_agreement / float(mode_len)
        avg_conf = float(np.mean([c for _, c in same_len_strings]))
        return consensus_str, avg_conf, float(avg_char_agreement)

    # Fallback to string with highest individual confidence
    highest_conf_item = max(cleaned, key=lambda x: x[1])
    return highest_conf_item[0], highest_conf_item[1], 0.5


def run_dot_matrix_ocr(
    image_crop: np.ndarray,
    parent_offset: Tuple[float, float],
    expected_field: str = "alphanumeric",
    engine_mgr: Optional[OCREngineManager] = None,
) -> List[OCRBox]:
    """
    Execute full dot-matrix OCR pipeline on a candidate image crop:
    1. Assess if region is likely dot-matrix
    2. Generate multiple preprocessing variants (upscaling, CLAHE, morphological dot bridging)
    3. Run field-aware OCR with targeted allowlists and geometry-selected PSMs
    4. Invert coordinates back to original image space
    5. Aggregate and return consensus OCRBoxes
    """
    if image_crop is None or image_crop.size == 0:
        return []

    mgr = engine_mgr or OCREngineManager()
    h, w = image_crop.shape[:2]
    offset_x, offset_y = parent_offset

    # Check dot matrix indicators
    report = detect_dot_matrix_region(image_crop)

    # Generate variants
    variants = generate_dot_matrix_variants(image_crop)

    # Allowlist applied post-hoc inside run_paddle() via character filtering.
    # PaddleOCR 3.x does not support inference-time character allowlists.
    allowlist = config.DOT_MATRIX_ALLOWLISTS.get(expected_field, config.DOT_MATRIX_ALLOWLISTS["alphanumeric"])
    apply_allowlist = allowlist if expected_field in {"date", "mrp"} else None

    raw_candidates: List[Tuple[str, float, BoundingBox]] = []

    for var_name, var_img, scale in variants:
        # Run PaddleOCR on variant (replaces EasyOCR + Tesseract dual-engine calls)
        try:
            p_boxes = mgr.run_paddle(
                var_img,
                variant=var_name,
                allowlist=apply_allowlist,
            )
            for pb in p_boxes:
                text_clean = normalize_confusable_characters(pb.text.strip(), expected_field)
                if text_clean:
                    # Map coordinates back to original image space
                    abs_bbox = BoundingBox(
                        x_min=offset_x + (pb.bbox.x_min / scale),
                        y_min=offset_y + (pb.bbox.y_min / scale),
                        x_max=offset_x + (pb.bbox.x_max / scale),
                        y_max=offset_y + (pb.bbox.y_max / scale),
                    )
                    raw_candidates.append((text_clean, pb.confidence, abs_bbox))
        except Exception:
            pass

    if not raw_candidates:
        return []

    # Cluster spatial candidates and perform character consensus
    # Group by vertical center proximity
    clusters: List[List[Tuple[str, float, BoundingBox]]] = []
    for cand in raw_candidates:
        placed = False
        for cl in clusters:
            ref_bbox = cl[0][2]
            if abs(cand[2].center_y - ref_bbox.center_y) <= max(15.0, ref_bbox.height * 0.6):
                cl.append(cand)
                placed = True
                break
        if not placed:
            clusters.append([cand])

    results: List[OCRBox] = []
    for cl in clusters:
        str_confs = [(c[0], c[1]) for c in cl]
        consensus_text, avg_conf, consensus_score = character_consensus_voting(str_confs, expected_field)
        if not consensus_text:
            continue

        # Merge bounding box
        x_min = min(c[2].x_min for c in cl)
        y_min = min(c[2].y_min for c in cl)
        x_max = max(c[2].x_max for c in cl)
        y_max = max(c[2].y_max for c in cl)

        # Boost confidence slightly if multi-variant consensus agreed
        final_conf = min(0.98, avg_conf * (0.85 + (0.15 * consensus_score)))

        box = OCRBox(
            text=consensus_text,
            bbox=BoundingBox(x_min, y_min, x_max, y_max),
            confidence=float(final_conf),
            engine="dot_matrix_consensus",
            variant="dot_matrix",
            raw_detection={
                "consensus_score": round(consensus_score, 2),
                "variant_count": len(cl),
                "dot_matrix_report": report.to_dict(),
            },
        )
        results.append(box)

    return results
