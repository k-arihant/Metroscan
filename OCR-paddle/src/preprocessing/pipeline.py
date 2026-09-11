"""
Adaptive image preprocessing pipeline.
Generates specialized preprocessing variants tailored to different text topologies:
- standard: general clean printed labels
- clahe: low-contrast/shiny/colored packaging
- dot_matrix: inkjet stamped batch/MRP/date text
- sharpened: small text / mild blur enhancement
"""
from typing import Dict, Optional, Tuple
import cv2
import numpy as np


def preprocess_standard(image: np.ndarray) -> np.ndarray:
    """Standard preprocessing: grayscale + edge-preserving bilateral filtering."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    # Bilateral filter smooths background noise while preserving sharp font edges
    denoised = cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)
    return denoised


def preprocess_clahe(image: np.ndarray, clip_limit: float = 2.5, tile_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """CLAHE preprocessing: locally enhances contrast on reflective packaging, foils, and colored labels."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
    enhanced = clahe.apply(gray)
    return enhanced


def preprocess_dot_matrix(image: np.ndarray) -> np.ndarray:
    """
    Specialized preprocessing for inkjet / dot-matrix stamped text (Batch, MRP, Dates).
    Uses CLAHE + subtle morphological closing to bridge disconnected ink dots
    without harsh binary thresholding.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Step 1: CLAHE to boost faint inkjet dots
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Step 2: Morphological closing with small 2x2 rectangular kernel
    # Bridges the microscopic air gaps between inkjet printer dots
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)

    return closed


def preprocess_sharpened(image: np.ndarray, max_dimension: int = 2400) -> np.ndarray:
    """
    Controlled upscale + unsharp masking for small or slightly blurred text.
    Enforces maximum dimension limit to avoid catastrophic memory/CPU explosions.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape[:2]
    # If image is small, upscale up to 1.5x-2x, but cap at max_dimension
    target_scale = 1.5
    if max(h, w) * target_scale > max_dimension:
        target_scale = max(1.0, max_dimension / max(h, w))

    if target_scale > 1.05:
        scaled = cv2.resize(gray, (int(w * target_scale), int(h * target_scale)), interpolation=cv2.INTER_CUBIC)
    else:
        scaled = gray

    # Unsharp masking: original + (original - blurred) * amount
    gaussian = cv2.GaussianBlur(scaled, (0, 0), sigmaX=2.0)
    sharpened = cv2.addWeighted(scaled, 1.4, gaussian, -0.4, 0)
    return sharpened


def generate_preprocessing_variants(image: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Generate the dictionary of preprocessed image variants for multi-pass OCR.
    """
    return {
        "standard": preprocess_standard(image),
        "clahe": preprocess_clahe(image),
        "dot_matrix": preprocess_dot_matrix(image),
        "sharpened": preprocess_sharpened(image),
    }
