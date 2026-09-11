"""
Multi-Pass OCR coordinator.
Orchestrates adaptive multi-variant PaddleOCR execution and delegates to aggregator.

Migration note: EasyOCR (Pass 1) and Tesseract (Pass 2) have been replaced by PaddleOCR.
  - Pass 1: PaddleOCR on 'standard' variant (baseline layout & word detection)
  - Pass 2: PaddleOCR on 'clahe' variant (contrast-enhanced, replaces Tesseract pass)
  - Pass 3: Dedicated Dot-Matrix Specialist Pass (unchanged logic, uses PaddleOCR internally)
The include_tesseract_pass parameter is retained for API compatibility but is now a no-op.
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
import config
from src.ocr.engine_manager import OCREngineManager, OCRBox
from src.ocr.aggregator import aggregate_ocr_results
from src.ocr.dot_matrix import detect_dot_matrix_region, run_dot_matrix_ocr
from src.preprocessing.pipeline import generate_preprocessing_variants


class MultiPassOCR:
    def __init__(self, engine_mgr: Optional[OCREngineManager] = None):
        self.engine_mgr = engine_mgr or OCREngineManager()

    def execute(
        self,
        image: np.ndarray,
        variants: Optional[Dict[str, np.ndarray]] = None,
        include_dot_matrix_pass: bool = True,
        include_tesseract_pass: bool = True,  # kept for API compatibility; no-op (Tesseract removed)
    ) -> Tuple[List[OCRBox], List[OCRBox]]:
        """
        Execute multi-pass OCR on image using preprocessed variants.
        Returns:
            (aggregated_words, aggregated_lines)
        """
        if variants is None:
            variants = generate_preprocessing_variants(image)

        pass_results: List[List[OCRBox]] = []

        # Pass 1: PaddleOCR on standard variant (baseline layout & words)
        standard_img = variants.get("standard", image)
        boxes_pass1 = self.engine_mgr.run_paddle(standard_img, variant="standard")
        pass_results.append(boxes_pass1)

        # Pass 2: PaddleOCR on CLAHE variant (contrast-enhanced; replaces old Tesseract pass)
        # Provides a second inference perspective to improve multi-variant consensus scoring.
        clahe_img = variants.get("clahe", standard_img)
        boxes_pass2 = self.engine_mgr.run_paddle(clahe_img, variant="clahe")
        if boxes_pass2:
            pass_results.append(boxes_pass2)

        # Pass 3: Dedicated Dot-Matrix Specialist Pass (Inkjet/dot stamps)
        if include_dot_matrix_pass and config.DOT_MATRIX_ENABLED:
            report = detect_dot_matrix_region(image)
            if report.is_dot_matrix:
                dot_boxes = run_dot_matrix_ocr(
                    image,
                    parent_offset=(0.0, 0.0),
                    expected_field="alphanumeric",
                    engine_mgr=self.engine_mgr,
                )
                if dot_boxes:
                    pass_results.append(dot_boxes)
            elif "dot_matrix" in variants:
                dot_img = variants["dot_matrix"]
                boxes_pass3 = self.engine_mgr.run_paddle(dot_img, variant="dot_matrix")
                if boxes_pass3:
                    pass_results.append(boxes_pass3)

        # Merge, score consensus agreement, and assemble line phrases
        aggregated_words, aggregated_lines = aggregate_ocr_results(pass_results)
        return aggregated_words, aggregated_lines
