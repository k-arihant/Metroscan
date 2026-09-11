"""
Image quality assessment module: blur, exposure, contrast, and resolution diagnostics.
Prevents pipeline from running on unreadable images and provides actionable feedback.
"""
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import cv2
import numpy as np
import config


@dataclass
class QualityReport:
    is_acceptable: bool
    blur_score: float
    blur_status: str
    mean_brightness: float
    brightness_status: str
    contrast_score: float
    contrast_status: str
    dimensions: Tuple[int, int]
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_acceptable": self.is_acceptable,
            "blur_score": round(self.blur_score, 2),
            "blur_status": self.blur_status,
            "mean_brightness": round(self.mean_brightness, 2),
            "brightness_status": self.brightness_status,
            "contrast_score": round(self.contrast_score, 2),
            "contrast_status": self.contrast_status,
            "dimensions": f"{self.dimensions[0]}x{self.dimensions[1]}",
            "issues": self.issues,
        }


def assess_image_quality(image: np.ndarray) -> QualityReport:
    """
    Assess quality of an input image for OCR readability.
    Args:
        image: BGR or grayscale numpy array
    Returns:
        QualityReport with objective scores and acceptability boolean.
    """
    if image is None or image.size == 0:
        return QualityReport(
            is_acceptable=False,
            blur_score=0.0,
            blur_status="INVALID",
            mean_brightness=0.0,
            brightness_status="INVALID",
            contrast_score=0.0,
            contrast_status="INVALID",
            dimensions=(0, 0),
            issues=["Image data is empty or corrupted."],
        )

    h, w = image.shape[:2]
    issues = []

    # Check minimum dimensions
    if w < config.MIN_IMAGE_DIMENSION or h < config.MIN_IMAGE_DIMENSION:
        issues.append(f"Image resolution too low ({w}x{h}). Minimum {config.MIN_IMAGE_DIMENSION}px required.")

    # Convert to grayscale for metric calculations
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 1. Blur estimation via Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    global_blur = float(laplacian.var())

    # For images with large blank backgrounds, check sharpness on top 10% highest-contrast blocks
    # Divide into 16 blocks (4x4)
    bh, bw = h // 4, w // 4
    block_vars = []
    for bi in range(4):
        for bj in range(4):
            block = gray[bi*bh:(bi+1)*bh, bj*bw:(bj+1)*bw]
            if block.size > 0 and block.std() > 15:
                block_vars.append(float(cv2.Laplacian(block, cv2.CV_64F).var()))

    if block_vars:
        # Use top 25th percentile of active blocks as text region sharpness
        block_vars.sort(reverse=True)
        top_k = max(1, len(block_vars) // 4)
        blur_score = float(np.mean(block_vars[:top_k]))
    else:
        blur_score = global_blur

    if blur_score < config.BLUR_THRESHOLD_SEVERE:
        blur_status = "SEVERE_BLUR"
        issues.append(f"Image is severely blurred (sharpness score: {blur_score:.1f}). Please capture a sharper image.")
    elif blur_score < config.BLUR_THRESHOLD_MODERATE:
        blur_status = "MODERATE_BLUR"
    else:
        blur_status = "SHARP"

    # 2. Exposure & brightness estimation
    mean_brightness = float(np.mean(gray))
    if mean_brightness < config.MIN_MEAN_BRIGHTNESS:
        brightness_status = "UNDEREXPOSED"
        issues.append(f"Image is too dark (brightness: {mean_brightness:.1f}/255).")
    elif mean_brightness > config.MAX_MEAN_BRIGHTNESS:
        brightness_status = "OVEREXPOSED"
        issues.append(f"Image is overexposed/washed out (brightness: {mean_brightness:.1f}/255).")
    else:
        brightness_status = "GOOD"

    # 3. RMS Contrast estimation
    contrast_score = float(gray.std())
    if contrast_score < config.LOW_CONTRAST_THRESHOLD:
        contrast_status = "LOW_CONTRAST"
        issues.append(f"Image contrast is very low (std dev: {contrast_score:.1f}).")
    else:
        contrast_status = "GOOD"

    # Strict acceptability criteria
    # If blur is severe or resolution is too small or extreme exposure, reject early
    is_acceptable = blur_status != "SEVERE_BLUR" and len(issues) == 0 or (
        blur_status != "SEVERE_BLUR" and brightness_status == "GOOD" and contrast_score >= config.LOW_CONTRAST_THRESHOLD
    )

    return QualityReport(
        is_acceptable=is_acceptable,
        blur_score=blur_score,
        blur_status=blur_status,
        mean_brightness=mean_brightness,
        brightness_status=brightness_status,
        contrast_score=contrast_score,
        contrast_status=contrast_status,
        dimensions=(w, h),
        issues=issues,
    )
