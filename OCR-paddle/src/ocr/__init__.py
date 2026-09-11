"""
OCR package: Engine management, multi-pass coordination, and result aggregation.
"""
from .engine_manager import OCREngineManager, OCRBox
from .multi_pass import MultiPassOCR
from .aggregator import aggregate_ocr_results, cluster_into_lines
from .dot_matrix import (
    detect_dot_matrix_region,
    generate_dot_matrix_variants,
    run_dot_matrix_ocr,
    character_consensus_voting,
    normalize_confusable_characters,
)

__all__ = [
    "OCREngineManager",
    "OCRBox",
    "MultiPassOCR",
    "aggregate_ocr_results",
    "cluster_into_lines",
    "detect_dot_matrix_region",
    "generate_dot_matrix_variants",
    "run_dot_matrix_ocr",
    "character_consensus_voting",
    "normalize_confusable_characters",
]
