"""
Automatic orientation detection and deskewing module.
Corrects 90°, 180°, and 270° rotations as well as fine angular skews (-45° to +45°).

Migration note: Tesseract (pytesseract) has been removed. Orientation scoring now uses
the shared PaddleOCR singleton via OCREngineManager.run_paddle_for_text().
The singleton is already initialized before this module is called in the pipeline.
"""
from typing import Tuple, Dict, Any, List
import cv2
import numpy as np
from src.ocr.engine_manager import OCREngineManager


# Well-known label keywords used to score text readability across 4 cardinal orientations
LABEL_KEYWORDS = {
    "mrp", "batch", "net", "exp", "mfg", "date", "lic", "price",
    "weight", "pkd", "use", "ingredients", "best", "before", "fssai",
    "marketed", "manufactured", "unit", "quantity", "customer", "care"
}


def rotate_cardinal(image: np.ndarray, angle: int) -> np.ndarray:
    """Rotate image by 0, 90, 180, or 270 degrees clockwise."""
    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image.copy()


def score_text_orientation(image: np.ndarray) -> Tuple[int, Dict[int, int]]:
    """
    Score 0°, 90°, 180°, and 270° rotations based on recognizable label keywords.
    Uses PaddleOCR (shared singleton) on a fast downscaled image with early-exit
    on a strong upright match.

    The OCREngineManager singleton is used directly so PaddleOCR is never
    re-initialized here — it is already initialized by the pipeline before
    this function is called.
    """
    engine_mgr = OCREngineManager()

    scores: Dict[int, int] = {}
    h, w = image.shape[:2]
    max_dim = 800
    scale = min(1.0, max_dim / max(h, w))
    downscaled = cv2.resize(image, (int(w * scale), int(h * scale))) if scale < 1.0 else image

    # Test 0° first. If high keyword count found, short-circuit immediately.
    try:
        text_0 = engine_mgr.run_paddle_for_text(downscaled)
        matches_0 = sum(1 for kw in LABEL_KEYWORDS if kw in text_0)
        scores[0] = matches_0
        if matches_0 >= 3:
            # High confidence that 0° is already upright
            return 0, scores
    except Exception:
        scores[0] = 0

    # Otherwise evaluate remaining 3 orientations
    for angle in [90, 180, 270]:
        rotated = rotate_cardinal(downscaled, angle)
        try:
            text = engine_mgr.run_paddle_for_text(rotated)
            matches = sum(1 for kw in LABEL_KEYWORDS if kw in text)
            scores[angle] = matches
        except Exception:
            scores[angle] = 0

    best_angle = max(scores, key=lambda a: scores[a])
    # Only rotate if the alternative angle is strictly better than 0°
    if scores[best_angle] > scores[0]:
        return best_angle, scores
    return 0, scores


def detect_fine_skew(image: np.ndarray, max_angle: float = 45.0) -> float:
    """
    Detect fine skew angle in degrees (-max_angle to +max_angle) using Hough line transform.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Downscale for fast line detection
    h, w = gray.shape[:2]
    scale = min(1.0, 1000 / max(h, w))
    if scale < 1.0:
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)))

    # Canny edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=60, maxLineGap=10)

    if lines is None:
        return 0.0

    angles = []
    for line in lines:
    # OpenCV may return HoughLinesP output as:
    # [x1, y1, x2, y2]
    # or:
    # [[x1, y1, x2, y2]]
     coords = np.asarray(line).reshape(-1)

     if coords.size < 4:
        continue

     x1, y1, x2, y2 = coords[:4]

     angle = np.degrees(
        np.arctan2(y2 - y1, x2 - x1)
     )

    # Keep only near-horizontal lines
     if -max_angle <= angle <= max_angle and abs(angle) > 1.5:
        angles.append(float(angle))
     if len(angles) < 4:
        return 0.0

    # Use median to resist outliers
    median_angle = float(np.median(angles))
    return median_angle


def rotate_free(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate image by arbitrary angle in degrees, expanding canvas so no content is clipped."""
    if abs(angle_deg) < 0.5:
        return image.copy()

    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    # Compute new bounding dimensions
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Adjust transformation matrix to account for translation
    matrix[0, 2] += (new_w / 2.0) - center[0]
    matrix[1, 2] += (new_h / 2.0) - center[1]

    return cv2.warpAffine(image, matrix, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def normalize_orientation(image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Perform 2-step orientation normalization:
    1. Cardinal 90°/180°/270° orientation alignment.
    2. Fine angular deskewing (only applied if skew is significant and not already confirmed upright).
    Returns normalized image and diagnostic metadata.
    """
    cardinal_angle, scores = score_text_orientation(image)
    oriented = rotate_cardinal(image, cardinal_angle)

    # Check if 0° was already strongly upright (3 or more keywords found)
    is_strongly_upright = scores.get(0, 0) >= 3 and cardinal_angle == 0

    fine_angle = detect_fine_skew(oriented)
    # Only apply fine deskew if skew is substantial (>= 8.0°) or if image was not already strongly upright
    min_deskew_threshold = 12.0 if is_strongly_upright else 6.0
    apply_deskew = abs(fine_angle) >= min_deskew_threshold

    if apply_deskew:
        deskewed = rotate_free(oriented, -fine_angle)
    else:
        deskewed = oriented

    metadata = {
        "cardinal_rotation": cardinal_angle,
        "orientation_scores": scores,
        "fine_skew_angle": round(fine_angle, 2),
        "fine_deskew_applied": apply_deskew,
        "total_rotation_applied": cardinal_angle + (-fine_angle if apply_deskew else 0.0),
    }

    return deskewed, metadata
