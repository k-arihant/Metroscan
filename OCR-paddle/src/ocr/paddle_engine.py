"""
PaddleOCR Engine Module.
-----------------------
Responsible for:
- Initializing PaddleOCR on NVIDIA GPU (singleton model reuse)
- Executing OCR inference
- Extracting raw recognized text, confidence, and polygon coordinates
- Converting polygons to axis-aligned bounding boxes in original image coordinates
- Returning normalized internal OCR detections in deterministic reading order
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Union, Optional
import cv2
import numpy as np

import config

logger = logging.getLogger(__name__)


class PaddleOCREngine:
    """
    Singleton engine wrapper around PaddleOCR.
    Loads models once on GPU (gpu:0) and reuses them across all single and batch inferences.
    """
    _instance: Optional["PaddleOCREngine"] = None
    _ocr: Any = None

    def __new__(cls) -> "PaddleOCREngine":
        if cls._instance is None:
            cls._instance = super(PaddleOCREngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self) -> None:
        """Initialize PaddleOCR singleton once with configured language and device."""
        try:
            from paddleocr import PaddleOCR
            lang = getattr(config, "PADDLE_LANG", "en")
            device = getattr(config, "PADDLE_DEVICE", "gpu:0")
            # Avoid UVDoc document warping which flattens 3D package pouches into uniform noise
            try:
                self._ocr = PaddleOCR(lang=lang, device=device, use_doc_orientation_classify=False, use_doc_unwarping=False)
            except TypeError:
                self._ocr = PaddleOCR(lang=lang, device=device)
            logger.info("PaddleOCREngine initialized: lang=%s, device=%s", lang, device)
        except Exception as exc:
            logger.error("Failed to initialize PaddleOCR: %s", exc)
            raise

    @staticmethod
    def _to_bgr_uint8(image: np.ndarray) -> np.ndarray:
        """Ensure numpy image array is uint8 BGR as expected by PaddleOCR."""
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    @staticmethod
    def polygon_to_bbox(poly: Any) -> Dict[str, int]:
        """
        Convert PaddleOCR 4-point polygon into an axis-aligned bounding box.
        Formula:
          x = min(all x)
          y = min(all y)
          right = max(all x)
          bottom = max(all y)
          width = right - x
          height = bottom - y
        """
        arr = np.asarray(poly, dtype=np.float32)
        if arr.ndim == 2 and arr.shape[0] >= 4 and arr.shape[1] == 2:
            min_x = float(np.min(arr[:, 0]))
            max_x = float(np.max(arr[:, 0]))
            min_y = float(np.min(arr[:, 1]))
            max_y = float(np.max(arr[:, 1]))
            x = int(round(min_x))
            y = int(round(min_y))
            width = max(0, int(round(max_x - min_x)))
            height = max(0, int(round(max_y - min_y)))
            return {"x": x, "y": y, "width": width, "height": height}
        raise ValueError(f"Invalid polygon shape: {arr.shape}")

    def detect_image(
        self,
        image_input: Union[str, Path, np.ndarray],
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Execute PaddleOCR on an image input and return normalized detections.

        Args:
            image_input: File path (str or Path) or OpenCV numpy array (BGR/gray).

        Returns:
            Tuple of:
              - List of normalized detection dicts:
                  [
                    {
                      "text": str,
                      "confidence": float,  # rounded to 4 decimals
                      "bbox": {"x": int, "y": int, "width": int, "height": int}
                    }, ...
                  ]
              - Image width (int)
              - Image height (int)
        """
        image_path: Optional[Path] = None
        if isinstance(image_input, (str, Path)):
            image_path = Path(image_input)
            if not image_path.exists():
                logger.error("Image file does not exist: %s", image_path)
                return [], 0, 0
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error("Failed to load image from file: %s", image_path)
                return [], 0, 0
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            logger.error("Unsupported image input type: %s", type(image_input))
            return [], 0, 0

        orig_h, orig_w = img.shape[:2]
        if orig_h == 0 or orig_w == 0:
            return [], 0, 0

        img_bgr = self._to_bgr_uint8(img)

        try:
            results = list(self._ocr.predict(img_bgr))
        except Exception as exc:
            logger.error("PaddleOCR prediction failed: %s", exc)
            return [], orig_w, orig_h

        detections: List[Dict[str, Any]] = []

        for res_obj in results:
            if res_obj is None:
                continue

            try:
                rec_texts = res_obj["rec_texts"]
                rec_scores = res_obj["rec_scores"]
                rec_polys = res_obj["rec_polys"]
            except (KeyError, TypeError) as exc:
                logger.warning("Unexpected OCRResult structure: %s", exc)
                continue

            for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
                if text is None:
                    continue
                cleaned_text = str(text).strip()
                if not cleaned_text:
                    continue

                try:
                    bbox = self.polygon_to_bbox(poly)
                except Exception as exc:
                    logger.debug("Failed to convert polygon to bbox: %s", exc)
                    continue

                conf = round(float(score), 4)

                detections.append({
                    "text": cleaned_text,
                    "confidence": conf,
                    "bbox": bbox,
                })

        # Deterministic spatial reading order: top-to-bottom, left-to-right
        detections.sort(key=lambda d: (d["bbox"]["y"], d["bbox"]["x"]))

        return detections, orig_w, orig_h
