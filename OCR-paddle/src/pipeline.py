"""
End-to-End Food/Product Label Compliance OCR Pipeline.
Orchestrates quality assessment, orientation normalization, multi-pass OCR,
spatial key-value extraction, semantic validation, and structured JSON output.
"""
from pathlib import Path
from typing import Union, Dict, Any, Optional, Tuple
import cv2
import numpy as np

import config
from src.utils.image_quality import assess_image_quality, QualityReport
from src.preprocessing.orientation import normalize_orientation
from src.preprocessing.pipeline import generate_preprocessing_variants
from src.ocr.engine_manager import OCREngineManager
from src.ocr.multi_pass import MultiPassOCR
from src.ocr.paddle_engine import PaddleOCREngine
from src.output.json_writer import build_ocr_json, save_ocr_json
from src.extraction.field_extractor import extract_all_fields
from src.output.builder import build_standardized_output


class LabelCompliancePipeline:
    def __init__(self, engine_mgr: Optional[OCREngineManager] = None):
        self.engine_mgr = engine_mgr or OCREngineManager()
        self.multi_pass = MultiPassOCR(self.engine_mgr)

    def process_image(
        self,
        image_input: Union[str, Path, np.ndarray],
        auto_orient: bool = True,
        include_dot_matrix_pass: bool = True,
        include_tesseract_pass: bool = True,
        calibration: Optional[Dict[str, Any]] = None,
        pdp: Optional[Dict[str, Any]] = None,
        package_id: Optional[str] = None,
        label_side: str = "back",
        blown_formed_moulded: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute full compliance extraction pipeline on an input image.
        Args:
            image_input: File path (str/Path) or OpenCV BGR numpy array
            auto_orient: Automatically detect 90°/180°/270° orientation and fine skew
            include_dot_matrix_pass: Run specialized morphological pass for stamped text
            include_tesseract_pass: Kept for API compatibility; no-op (Tesseract removed)
            calibration: Physical calibration dict with 'pixels_per_mm', 'source', 'confidence'
            pdp: Principal Display Panel dict with 'area_cm2', 'width_cm', 'height_cm'
            package_id: Optional custom package identifier
            label_side: Label side identifier (e.g. 'front', 'back')
            blown_formed_moulded: Flag indicating blown/formed/moulded container
        Returns:
            Authoritative standardized JSON dictionary conforming to compliance schema.
        """
        image_name = "image_array"
        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            image_name = img_path.name
            image = cv2.imread(str(img_path))
            if image is None:
                return build_standardized_output(
                    image_filename=image_name,
                    image=None,
                    lines=[],
                    words=[],
                    field_result={
                        "ocr_status": "error",
                        "error_message": f"Failed to load image from path: {img_path}",
                        "fields": {},
                        "confidence": {},
                        "uncertain_fields": config.RECOGNIZED_FIELDS,
                    },
                    package_id=package_id,
                    label_side=label_side,
                    calibration=calibration,
                    pdp=pdp,
                    blown_formed_moulded=blown_formed_moulded,
                )
        else:
            image = image_input

        # -------------------------------------------------------------
        # Step 1: Image Quality Assessment
        # -------------------------------------------------------------
        quality: QualityReport = assess_image_quality(image)
        if not quality.is_acceptable and quality.blur_status == "SEVERE_BLUR":
            return build_standardized_output(
                image_filename=image_name,
                image=image,
                lines=[],
                words=[],
                field_result={
                    "ocr_status": "insufficient_quality",
                    "error_message": "Image quality insufficient for reliable OCR. Please capture a closer, sharper image.",
                    "fields": {k: None for k in config.RECOGNIZED_FIELDS},
                    "confidence": {k: 0.0 for k in config.RECOGNIZED_FIELDS},
                    "uncertain_fields": config.RECOGNIZED_FIELDS,
                },
                quality_report=quality,
                package_id=package_id,
                label_side=label_side,
                calibration=calibration,
                pdp=pdp,
                blown_formed_moulded=blown_formed_moulded,
            )

        # -------------------------------------------------------------
        # Step 2: Orientation Normalization & Deskewing
        # -------------------------------------------------------------
        orientation_meta = {}
        if auto_orient:
            processed_img, orientation_meta = normalize_orientation(image)
        else:
            processed_img = image.copy()

        # -------------------------------------------------------------
        # Step 3: Adaptive Preprocessing Variants
        # -------------------------------------------------------------
        variants = generate_preprocessing_variants(processed_img)

        # -------------------------------------------------------------
        # Step 4: Multi-Pass OCR & Aggregation
        # -------------------------------------------------------------
        words, lines = self.multi_pass.execute(
            processed_img,
            variants=variants,
            include_dot_matrix_pass=include_dot_matrix_pass,
            include_tesseract_pass=include_tesseract_pass,
        )

        if not lines and not words:
            return build_standardized_output(
                image_filename=image_name,
                image=processed_img,
                lines=[],
                words=[],
                field_result={
                    "ocr_status": "no_text_detected",
                    "fields": {k: None for k in config.RECOGNIZED_FIELDS},
                    "confidence": {k: 0.0 for k in config.RECOGNIZED_FIELDS},
                    "uncertain_fields": config.RECOGNIZED_FIELDS,
                },
                quality_report=quality,
                orientation_meta=orientation_meta,
                package_id=package_id,
                label_side=label_side,
                calibration=calibration,
                pdp=pdp,
                blown_formed_moulded=blown_formed_moulded,
            )

        # -------------------------------------------------------------
        # Step 5: Spatial Key-Value Extraction & Legal Metrology Validation
        # -------------------------------------------------------------
        result = extract_all_fields(
            lines,
            words,
            image_filename=image_name,
            image=processed_img,
            engine_mgr=self.engine_mgr,
        )

        # Attach image diagnostics into intermediate result
        result["quality_report"] = quality.to_dict()
        result["orientation"] = orientation_meta
        result["total_detected_words"] = len(words)
        result["total_detected_lines"] = len(lines)

        # -------------------------------------------------------------
        # Step 6: Standardized Output Builder with Regulatory Evaluation
        # -------------------------------------------------------------
        return build_standardized_output(
            image_filename=image_name,
            image=processed_img,
            lines=lines,
            words=words,
            field_result=result,
            layout_struct=result.get("layout"),
            quality_report=quality,
            orientation_meta=orientation_meta,
            calibration=calibration,
            pdp=pdp,
            package_id=package_id,
            label_side=label_side,
            blown_formed_moulded=blown_formed_moulded,
        )


class PaddleOCRPipeline:
    """
    Pipeline for raw PaddleOCR inference and standardized JSON generation.

    Data flow:
      Image -> PaddleOCREngine -> Normalized Detections -> build_ocr_json -> save_ocr_json -> output/<stem>_ocr.json
    """
    def __init__(self, engine: Optional[PaddleOCREngine] = None):
        self.engine = engine or PaddleOCREngine()

    def process_image(
        self,
        image_input: Union[str, Path, np.ndarray],
        output_dir: Union[str, Path] = "output",
        package_id: Optional[str] = None,
        label_side: str = "unknown",
    ) -> Tuple[Dict[str, Any], Path]:
        """
        Execute PaddleOCR, build standard raw JSON, and save to output/<stem>_ocr.json.
        Handles empty results and errors gracefully by generating valid JSON.
        """
        path_obj = Path(image_input) if isinstance(image_input, (str, Path)) else None
        image_name = path_obj.name if path_obj else "image_array"

        try:
            detections, width, height = self.engine.detect_image(image_input)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("Error processing image %s: %s", image_name, exc)
            detections, width, height = [], 0, 0

        json_result = build_ocr_json(
            image_name_or_path=image_name,
            width=width,
            height=height,
            detections=detections,
            package_id=package_id,
            label_side=label_side,
        )

        saved_path = save_ocr_json(
            json_result,
            image_name_or_path=image_name,
            output_dir=output_dir,
        )

        return json_result, saved_path


def process_paddle_ocr(
    image_input: Union[str, Path, np.ndarray],
    output_dir: Union[str, Path] = "output",
    package_id: Optional[str] = None,
    label_side: str = "unknown",
) -> Tuple[Dict[str, Any], Path]:
    """Convenience function to run the PaddleOCRPipeline on an image."""
    pipeline = PaddleOCRPipeline()
    return pipeline.process_image(
        image_input,
        output_dir=output_dir,
        package_id=package_id,
        label_side=label_side,
    )

