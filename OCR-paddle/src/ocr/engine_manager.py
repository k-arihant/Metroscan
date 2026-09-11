"""
OCR Engine Manager: Singleton management of PaddleOCR GPU.
Provides unified OCRBox representation preserving text, bbox, confidence, and engine metadata.

PaddleOCR 3.7.0 API (verified by live inference inspection):
  - Initialized with PaddleOCR(lang=..., device='gpu:0')
  - Inference via paddle_ocr.predict(image) → list of OCRResult objects
  - OCRResult is dict-like with keys:
      'rec_texts'  : list[str]
      'rec_scores' : list[float]           # 0.0 to 1.0
      'rec_polys'  : list[[[x,y],...]]     # 4-point polygon per detection
      'rec_boxes'  : list[[x1,y1,x2,y2]]  # axis-aligned bbox per detection
  - Allowlists: NOT supported at inference time. Applied post-hoc via character filtering.
    Note: Post-hoc filtering removes disallowed characters but cannot change model
    decoding decisions (the model may merge/split characters differently than with
    a constrained decoder). This is documented behavior for PaddleOCR 3.x.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Any
import cv2
import numpy as np

import config
from src.utils.geometry import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class OCRBox:
    text: str
    bbox: BoundingBox
    confidence: float
    engine: str      # 'paddle'
    variant: str     # 'standard', 'clahe', 'dot_matrix', etc.
    raw_detection: Any = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "confidence": round(self.confidence, 3),
            "engine": self.engine,
            "variant": self.variant,
        }


def _apply_allowlist_postprocess(text: str, allowlist: Optional[str]) -> str:
    """
    Apply character-level allowlist filtering as post-processing.

    PaddleOCR 3.x does not support inference-time character allowlists.
    This function strips characters not in the allowlist from the detected text,
    providing a best-effort approximation of the old EasyOCR/Tesseract behavior.

    Limitation: The model may decode character sequences differently than it
    would with a constrained CTC/attention decoder. The post-hoc filter
    removes characters but cannot undo incorrect character merges.
    """
    if not allowlist or not text:
        return text
    allowed = set(allowlist)
    return "".join(ch for ch in text if ch in allowed).strip()


class OCREngineManager:
    """
    Singleton OCR engine manager backed by PaddleOCR 3.7.0 GPU.

    The PaddleOCR model is initialized ONCE and reused for ALL inference:
    multi-pass OCR, dot-matrix passes, and orientation scoring.
    Never re-initialized per image or per rotation.
    """
    _instance: Optional["OCREngineManager"] = None
    _paddle_ocr: Any = None

    def __new__(cls) -> "OCREngineManager":
        if cls._instance is None:
            cls._instance = super(OCREngineManager, cls).__new__(cls)
            cls._instance._init_engines()
        return cls._instance

    def _init_engines(self) -> None:
        """Initialize PaddleOCR singleton once on first instantiation."""
        try:
            from paddleocr import PaddleOCR
            self._paddle_ocr = PaddleOCR(
                lang=config.PADDLE_LANG,
                device=config.PADDLE_DEVICE,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
            )
            logger.info(
                "PaddleOCR initialized: lang=%s, device=%s",
                config.PADDLE_LANG,
                config.PADDLE_DEVICE,
            )
        except Exception as exc:
            logger.error("Failed to initialize PaddleOCR: %s", exc)
            raise

    def _to_bgr_uint8(self, image: np.ndarray) -> np.ndarray:
        """Ensure image is uint8 BGR as expected by PaddleOCR predict()."""
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    def _parse_ocr_result(
        self,
        result_obj: Any,
        variant: str,
        allowlist: Optional[str] = None,
    ) -> List[OCRBox]:
        """
        Normalize a PaddleOCR 3.7.0 OCRResult dict-like object into OCRBox list.

        Keys used (verified against live inference output):
          rec_texts  : list[str]
          rec_scores : list[float]
          rec_polys  : list[[[x,y],[x,y],[x,y],[x,y]]]
        """
        boxes: List[OCRBox] = []
        try:
            rec_texts = result_obj["rec_texts"]
            rec_scores = result_obj["rec_scores"]
            rec_polys = result_obj["rec_polys"]
        except (KeyError, TypeError) as exc:
            logger.warning("Unexpected OCRResult structure: %s", exc)
            return boxes

        if not rec_texts:
            return boxes

        for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
            cleaned = text.strip()
            if not cleaned:
                continue
            if allowlist:
                cleaned = _apply_allowlist_postprocess(cleaned, allowlist)
                if not cleaned:
                    continue
            try:
                bbox = BoundingBox.from_polygon(poly)
                boxes.append(OCRBox(
                    text=cleaned,
                    bbox=bbox,
                    confidence=float(score),
                    engine="paddle",
                    variant=variant,
                    raw_detection={"poly": poly, "score": score},
                ))
            except Exception as exc:
                logger.debug("Skipping OCR box (parse error): %s", exc)
                continue

        return boxes

    def run_paddle(
        self,
        image: np.ndarray,
        variant: str = "standard",
        allowlist: Optional[str] = None,
    ) -> List[OCRBox]:
        """
        Execute PaddleOCR on a preprocessed image variant.

        Args:
            image:     OpenCV BGR or grayscale numpy array (uint8 preferred).
            variant:   Preprocessing variant tag (e.g. 'standard', 'clahe').
            allowlist: Optional character allowlist string. Applied post-hoc:
                       characters not in the set are stripped from each detected
                       text token. See _apply_allowlist_postprocess() for details.

        Returns:
            List of OCRBox instances in original image coordinate space.
        """
        if image is None or image.size == 0:
            return []

        img_bgr = self._to_bgr_uint8(image)

        try:
            results = list(self._paddle_ocr.predict(img_bgr))
        except Exception as exc:
            logger.warning("PaddleOCR inference failed on variant '%s': %s", variant, exc)
            return []

        boxes: List[OCRBox] = []
        for res_obj in results:
            if res_obj is None:
                continue
            boxes.extend(self._parse_ocr_result(res_obj, variant=variant, allowlist=allowlist))

        return boxes

    def run_paddle_for_text(self, image: np.ndarray) -> str:
        """
        Run PaddleOCR and return all detected text as a single concatenated
        lowercase string. Used for orientation scoring (keyword counting).
        The singleton model is reused — never re-initialized.
        """
        if image is None or image.size == 0:
            return ""

        img_bgr = self._to_bgr_uint8(image)

        try:
            results = list(self._paddle_ocr.predict(img_bgr))
        except Exception as exc:
            logger.warning("PaddleOCR text-only inference failed: %s", exc)
            return ""

        texts: List[str] = []
        for res_obj in results:
            if res_obj is None:
                continue
            try:
                texts.extend(res_obj["rec_texts"])
            except (KeyError, TypeError):
                pass

        return " ".join(t.lower() for t in texts if t)
