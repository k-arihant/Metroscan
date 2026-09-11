"""
Preprocessing package: orientation normalization, deskewing, and adaptive variants.
"""
from .orientation import normalize_orientation, score_text_orientation, detect_fine_skew
from .pipeline import (
    generate_preprocessing_variants,
    preprocess_standard,
    preprocess_clahe,
    preprocess_dot_matrix,
    preprocess_sharpened,
)

__all__ = [
    "normalize_orientation",
    "score_text_orientation",
    "detect_fine_skew",
    "generate_preprocessing_variants",
    "preprocess_standard",
    "preprocess_clahe",
    "preprocess_dot_matrix",
    "preprocess_sharpened",
]
