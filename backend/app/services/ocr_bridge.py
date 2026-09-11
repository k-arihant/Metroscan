"""
OCR Bridge: Integrates the teammate's modular OCR-paddle engine into the MetroScan backend.

Architecture:
  PRIMARY: PaddleOCREngine (OCR-paddle) — used when GPU model works correctly
  FALLBACK: Gemini Vision OCR — used when PaddleOCR returns 0 detections
             Gemini Vision reads the actual images and extracts all visible text.

Maintains the exact data contract:
Input:  list of local image paths (1-6 images)
Output: standardized dictionary conforming to sampleinput.json format:
        {
          "package_id": "pkg_...",
          "images": [...],
          "reference_objects": [...],
          "detections": [
             {
               "detection_id": "det_0001",
               "source_image_id": "img_000",
               "text": "...",
               "confidence": 0.98,
               "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 30}
             }, ...
          ],
          "quality_reports": [...]
        }
"""

import os
import sys
import uuid
import time
import json
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Dynamic Path Resolution ──
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent
OCR_PADDLE_DIR = PROJECT_ROOT / "OCR-paddle"

if OCR_PADDLE_DIR.exists() and str(OCR_PADDLE_DIR) not in sys.path:
    sys.path.insert(0, str(OCR_PADDLE_DIR))
    logger.info("Added OCR-paddle to sys.path: %s", OCR_PADDLE_DIR)


_VISION_MODEL_FALLBACK_CHAIN = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]


def _safe_parse_vision_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    Robustly parses the Gemini Vision JSON output.
    Returns list of dicts: [{"text": str, "box_2d": list|dict|None, "image_index": int}]
    Uses standard json.loads first, but gracefully falls back to regex recovery
    if Gemini output contains unescaped quotes or minor JSON syntax errors.
    """
    import re
    items: List[Dict[str, Any]] = []
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()

    # 1. Standard json.loads
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    t = item.get("text") or item.get("label") or ""
                    box = item.get("box_2d") or item.get("bounding_box")
                    img_idx = item.get("image_index", 0)
                    try:
                        img_idx = int(img_idx)
                    except Exception:
                        img_idx = 0
                    if t and str(t).strip():
                        items.append({"text": str(t).strip(), "box_2d": box, "image_index": img_idx})
                elif isinstance(item, str) and item.strip():
                    items.append({"text": item.strip(), "box_2d": None, "image_index": 0})
        elif isinstance(parsed, dict):
            raw_list = parsed.get("texts") or parsed.get("detections") or parsed.get("items") or []
            for item in raw_list:
                if isinstance(item, dict):
                    t = item.get("text") or item.get("label") or ""
                    box = item.get("box_2d") or item.get("bounding_box")
                    img_idx = item.get("image_index", 0)
                    try:
                        img_idx = int(img_idx)
                    except Exception:
                        img_idx = 0
                    if t and str(t).strip():
                        items.append({"text": str(t).strip(), "box_2d": box, "image_index": img_idx})
                elif isinstance(item, str) and item.strip():
                    items.append({"text": item.strip(), "box_2d": None, "image_index": 0})
        if items:
            return items
    except Exception as exc:
        logger.debug("json.loads failed on Vision response (%s). Applying regex recovery.", exc)

    # 2. Block-level regex parser for each object {...}
    for block_match in re.finditer(r'\{([^{}]+)\}', clean):
        block = block_match.group(1)
        t_m = re.search(r'"text"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', block)
        if not t_m:
            t_m = re.search(r'"text"\s*:\s*"(.*?)"', block)
        t = t_m.group(1).replace(r'\"', '"').strip() if t_m else ""

        idx_m = re.search(r'"image_index"\s*:\s*(\d+)', block)
        img_idx = int(idx_m.group(1)) if idx_m else 0

        box = None
        b_m = re.search(r'"box_2d"\s*:\s*\[([0-9\s,\.]+)\]', block)
        if b_m:
            try:
                coords = [float(x.strip()) for x in b_m.group(1).split(",") if x.strip()]
                if len(coords) == 4:
                    box = coords
            except Exception:
                pass
        if t:
            items.append({"text": t, "box_2d": box, "image_index": img_idx})

    # 3. Simple text regex fallback
    if not items:
        for t in re.findall(r'"text"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', clean):
            if t.strip():
                items.append({"text": t.replace(r'\"', '"').strip(), "box_2d": None, "image_index": 0})

    return items


def _gemini_vision_ocr(
    image_paths: List[str],
    api_key: str,
    pkg_id: str,
    label_sides: List[str],
) -> List[Dict[str, Any]]:
    """
    Use Gemini Vision to extract all visible text from the uploaded images.
    Returns a flat list of detection dicts (same schema as PaddleOCR output).

    Optimized Strategy:
      - Batches all images into a single multi-image Vision prompt (consumes 1 API call).
      - Multi-model fallback chain: gemini-3.5-flash -> gemini-3.5-flash-lite -> gemini-3.7-flash -> gemini-flash-latest.
      - Graceful quota (429) and high-demand (503) error switching across models.
      - Per-image pixel coordinate scaling using actual image dimensions.
    """
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        logger.error("google-genai not installed. Cannot use Gemini Vision OCR fallback.")
        return []

    if not api_key:
        logger.error("GEMINI_API_KEY not set. Cannot use Gemini Vision OCR fallback.")
        return []

    client = genai.Client(api_key=api_key)

    # Determine image dimensions & build contents
    img_dims: Dict[int, Tuple[int, int]] = {}
    contents: List[Any] = []
    valid_indices: List[int] = []

    for idx, img_path_str in enumerate(image_paths):
        img_path = Path(img_path_str)
        if not img_path.exists():
            logger.warning("Gemini Vision OCR: image not found: %s", img_path_str)
            continue

        w, h = 1000, 1000
        try:
            from PIL import Image
            with Image.open(img_path) as pil_img:
                w, h = pil_img.size
        except Exception:
            pass
        img_dims[idx] = (w, h)

        suffix = img_path.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(suffix, "image/jpeg")

        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            contents.append(genai_types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
            valid_indices.append(idx)
        except Exception as e:
            logger.error("Failed to read image %s: %s", img_path_str, e)

    if not contents:
        return []

    num_images = len(contents)
    if num_images == 1:
        vision_prompt = (
            "You are an expert OCR system for packaged commodity labels in India.\n"
            "Extract ALL visible text from this packaging image.\n"
            "Be thorough and capture ALL text: Brand name, Common/Generic commodity name, Net Quantity, "
            "MRP, taxes, dates (manufacturing, packing, expiry, best before), batch/lot numbers, "
            "manufacturer/packer name and complete address, consumer care (phone, email, website), "
            "FSSAI license numbers, barcodes, ingredients.\n"
            "Preserve original text, capitalization, numbers, units, and punctuation.\n"
            "Return a JSON array of objects, where each object has:\n"
            "  - \"image_index\": 0\n"
            "  - \"text\": string with the exact text segment as written\n"
            "  - \"box_2d\": [ymin, xmin, ymax, xmax] coordinates normalized to 0-1000\n"
            "Return STRICT JSON array only. No markdown formatting."
        )
    else:
        vision_prompt = (
            f"You are an expert OCR system for packaged commodity labels in India.\n"
            f"You are given {num_images} images of a packaged commodity (Image 0 to Image {num_images - 1}).\n"
            f"Extract ALL visible text from each image: Brand name, Common/Generic commodity name, Net Quantity, "
            f"MRP, taxes, dates (manufacturing, packing, expiry, best before), batch/lot numbers, "
            f"manufacturer/packer name and complete address, consumer care (phone, email, website), "
            f"FSSAI license numbers, barcodes, ingredients.\n"
            f"Preserve original text, capitalization, numbers, units, and punctuation.\n"
            f"Return a JSON array of objects, where each object has:\n"
            f"  - \"image_index\": integer corresponding to which image this text is from (0 to {num_images - 1})\n"
            f"  - \"text\": string with the exact text segment as written\n"
            f"  - \"box_2d\": [ymin, xmin, ymax, xmax] coordinates normalized to 0-1000 for that specific image\n"
            f"Return STRICT JSON array only. No markdown formatting."
        )

    contents.append(vision_prompt)

    items: List[Dict[str, Any]] = []
    for model_name in _VISION_MODEL_FALLBACK_CHAIN:
        for attempt in range(2):
            try:
                logger.info("Gemini Vision OCR calling %s (attempt %d)...", model_name, attempt + 1)
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )
                items = _safe_parse_vision_json(response.text)
                if items:
                    logger.info("Gemini Vision OCR succeeded with %s: %d text segments extracted", model_name, len(items))
                    break
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    logger.warning("Gemini Vision model %s hit quota (429), switching to next model...", model_name)
                    break
                if ("503" in err or "UNAVAILABLE" in err or "high demand" in err) and attempt < 1:
                    logger.warning("Gemini Vision model %s returned 503, retrying in 2s...", model_name)
                    time.sleep(2)
                    continue
                logger.warning("Gemini Vision model %s failed: %s", model_name, e)
                break
        if items:
            break

    all_detections: List[Dict[str, Any]] = []
    det_counter = 0

    for item in items:
        text = item.get("text", "")
        box = item.get("box_2d")
        raw_idx = item.get("image_index", 0)
        # Map to original image index in image_paths
        actual_idx = valid_indices[raw_idx] if 0 <= raw_idx < len(valid_indices) else 0

        img_id = f"img_{actual_idx:03d}"
        side = label_sides[actual_idx] if actual_idx < len(label_sides) else "unspecified"
        img_w, img_h = img_dims.get(actual_idx, (1000, 1000))

        det_counter += 1
        bbox = {"x": 0, "y": 0, "width": 0, "height": 0}
        if box and isinstance(box, list) and len(box) == 4:
            try:
                ymin, xmin, ymax, xmax = [float(c) for c in box]
                bx = int(round(xmin * img_w / 1000.0))
                by = int(round(ymin * img_h / 1000.0))
                bw = max(1, int(round((xmax - xmin) * img_w / 1000.0)))
                bh = max(1, int(round((ymax - ymin) * img_h / 1000.0)))
                bbox = {"x": bx, "y": by, "width": bw, "height": bh}
            except Exception:
                pass
        elif isinstance(box, dict):
            bbox = {
                "x": int(box.get("x", 0)),
                "y": int(box.get("y", 0)),
                "width": int(box.get("width", 0)),
                "height": int(box.get("height", 0)),
            }

        all_detections.append({
            "detection_id": f"det_{det_counter:04d}",
            "source_image_id": img_id,
            "text": text,
            "confidence": 0.95,
            "bounding_box": bbox,
            "_source": "gemini_vision",
            "_label_side": side,
        })

    logger.info(
        "Gemini Vision OCR complete: %d total detections across %d image(s)",
        len(all_detections), len(image_paths)
    )
    return all_detections


def _is_useful_ocr_result(detections: List[Dict[str, Any]]) -> bool:
    """
    Validates whether OCR detections contain genuine, readable packaged-commodity text
    (Latin alphabet / Devanagari Hindi / digits) rather than corrupted GPU output
    (e.g., CJK ideographs produced by PP-OCRv6 recognition weights on Blackwell Compute 12.0).
    """
    if not detections:
        return False

    import re
    total_valid_chars = 0
    total_corrupt_chars = 0
    valid_words = 0

    for d in detections:
        t = str(d.get("text", "")).strip()
        if not t:
            continue
        # Latin alphanumeric characters, digits, standard punctuation
        valid_chars = len(re.findall(r'[a-zA-Z0-9\s.,/():₹$%\-–—]', t))
        # CJK ideographs characteristic of GPU memory/kernel corruption on Compute 12.0
        corrupt_chars = len([c for c in t if 0x2E80 <= ord(c) <= 0x9FFF])

        total_valid_chars += valid_chars
        total_corrupt_chars += corrupt_chars

        # Words with 2 or more letters
        words = re.findall(r'[a-zA-Z]{2,}', t)
        valid_words += len(words)

    # Corrupted output check: corrupt CJK characters outnumber valid Latin characters
    if total_corrupt_chars > total_valid_chars:
        return False

    # Meaningful text check: must have at least 3 recognizable words across the package
    if valid_words < 3 and len(detections) < 15:
        return False

    return True


def detect_reference_barcodes(
    image_paths: List[str],
    label_sides: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect physical reference barcodes (e.g. EAN-13, UPC) across all package images.
    Uses OpenCV's cv2.barcode.BarcodeDetector with multi-angle rotation (0°, 90°, 180°, 270°)
    and sub-region decoding enhancement.

    Returns a list of standardized ReferenceObject dictionaries conforming to the schema:
    [
        {
            "type": "ean_13_barcode",
            "value": str or None,  # decoded digits if decodable
            "source_image_id": "img_000",
            "bounding_box": {"x": int, "y": int, "width": int, "height": int},
            "barcode_width_px": int,  # standard width dimension across bars
            "points": [[x, y], ...],
        }
    ]
    """
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV not installed. Cannot perform barcode reference detection.")
        return []

    if not hasattr(cv2, "barcode") or not hasattr(cv2.barcode, "BarcodeDetector"):
        logger.warning("OpenCV barcode module not available. Cannot perform barcode reference detection.")
        return []

    detector = cv2.barcode.BarcodeDetector()
    reference_objects: List[Dict[str, Any]] = []
    seen_bboxes = set()

    for idx, img_path_str in enumerate(image_paths):
        img_path = Path(img_path_str)
        if not img_path.exists():
            continue

        img_id = f"img_{idx:03d}"
        cv_img = cv2.imread(str(img_path))
        if cv_img is None:
            continue

        h_img, w_img = cv_img.shape[:2]

        # Try multiple rotations: 0, 90, 180, 270 degrees
        # (Products might be photographed at any angle)
        angles = [0, 90, 180, 270]
        detected_for_image = False

        for angle in angles:
            if angle == 0:
                cur_img = cv_img
            elif angle == 90:
                cur_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
            elif angle == 180:
                cur_img = cv2.rotate(cv_img, cv2.ROTATE_180)
            elif angle == 270:
                cur_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            h_cur, w_cur = cur_img.shape[:2]

            try:
                ret, points = detector.detect(cur_img)
            except Exception as e:
                logger.debug("cv2.barcode.BarcodeDetector.detect error on %s at angle %d: %s", img_path.name, angle, e)
                ret, points = False, None

            if ret and points is not None and len(points) > 0:
                for pts in points:
                    if len(pts) < 4:
                        continue

                    # Transform points back to original 0-degree coordinate space if rotated
                    orig_pts = []
                    for pt in pts:
                        x, y = float(pt[0]), float(pt[1])
                        if angle == 90:
                            # (x, y) in 90-deg image -> rotated clockwise:
                            orig_x = y
                            orig_y = h_img - 1 - x
                        elif angle == 180:
                            orig_x = w_img - 1 - x
                            orig_y = h_img - 1 - y
                        elif angle == 270:
                            # (x, y) in 270-deg image -> rotated 90 counter-clockwise:
                            orig_x = w_img - 1 - y
                            orig_y = x
                        else:
                            orig_x = x
                            orig_y = y
                        orig_pts.append([orig_x, orig_y])

                    xs = [p[0] for p in orig_pts]
                    ys = [p[1] for p in orig_pts]
                    bx = max(0, int(round(min(xs))))
                    by = max(0, int(round(min(ys))))
                    bw = max(1, int(round(max(xs) - min(xs))))
                    bh = max(1, int(round(max(ys) - min(ys))))

                    # Deduplicate if overlapping with an already detected barcode on this image
                    box_key = (img_id, bx // 10, by // 10, bw // 10, bh // 10)
                    if box_key in seen_bboxes:
                        continue
                    seen_bboxes.add(box_key)

                    # In standard GS1 EAN-13 barcodes, the bars span across the larger dimension
                    # (nominal width is 37.29 mm across all 95 modules / bars & spaces)
                    barcode_width_px = max(bw, bh)

                    # Attempt decoding by cropping the barcode with margin and upscaling
                    decoded_value = None
                    try:
                        pad = 20
                        x1, y1 = max(0, bx - pad), max(0, by - pad)
                        x2, y2 = min(w_img, bx + bw + pad), min(h_img, by + bh + pad)
                        crop = cv_img[y1:y2, x1:x2]
                        if crop.size > 0:
                            # 2x cubic upscaling significantly improves barcode decoding accuracy
                            crop_up = cv2.resize(crop, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                            res = detector.detectAndDecode(crop_up)
                            if res and res[0] and str(res[0]).strip():
                                decoded_value = str(res[0]).strip()
                    except Exception as dec_err:
                        logger.debug("Barcode decoding error on crop: %s", dec_err)

                    ref_obj = {
                        "type": "ean_13_barcode",
                        "value": decoded_value,
                        "source_image_id": img_id,
                        "bounding_box": {
                            "x": bx,
                            "y": by,
                            "width": bw,
                            "height": bh,
                        },
                        "barcode_width_px": barcode_width_px,
                        "points": orig_pts,
                    }
                    reference_objects.append(ref_obj)
                    logger.info(
                        "Detected physical reference barcode on %s (%s): bbox=%s, width_px=%d, decoded=%s",
                        img_path.name, img_id, ref_obj["bounding_box"], barcode_width_px, decoded_value
                    )
                    detected_for_image = True

            if detected_for_image:
                break

    return reference_objects


class OCRBridge:
    """
    Singleton Bridge managing inference via OCR-paddle with Gemini Vision fallback.

    Strategy:
      1. Try PaddleOCREngine (GPU-based, fast)
      2. If PaddleOCR returns 0 detections, fall back to Gemini Vision
      3. Combined detections flow through the same downstream pipeline
    """
    _instance: Optional["OCRBridge"] = None
    _engine = None
    _engine_initialized: bool = False
    _init_error: Optional[str] = None

    def __new__(cls) -> "OCRBridge":
        if cls._instance is None:
            cls._instance = super(OCRBridge, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_engine(cls):
        """Lazy singleton loader for PaddleOCREngine."""
        if not cls._engine_initialized:
            try:
                if OCR_PADDLE_DIR.exists() and str(OCR_PADDLE_DIR) not in sys.path:
                    sys.path.insert(0, str(OCR_PADDLE_DIR))

                from src.ocr.paddle_engine import PaddleOCREngine
                cls._engine = PaddleOCREngine()
                cls._engine_initialized = True
                cls._init_error = None
                logger.info("OCRBridge: PaddleOCREngine initialized successfully.")
            except Exception as exc:
                cls._init_error = str(exc)
                logger.warning(
                    "OCRBridge: PaddleOCREngine could not be initialized (%s). "
                    "Will use Gemini Vision OCR fallback.",
                    exc
                )
        return cls._engine

    @classmethod
    def run_ocr(
        cls,
        image_paths: List[str],
        package_id: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        label_sides: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute OCR across 1-6 package images.
        Primary: PaddleOCREngine. Fallback: Gemini Vision.

        Returns structured dictionary matching the sampleinput.json specification.
        """
        try:
            import cv2
            has_cv2 = True
        except ImportError:
            cv2 = None
            has_cv2 = False

        pkg_id = package_id or f"pkg_{uuid.uuid4().hex[:10]}"
        default_sides = ["front", "back", "mrp_panel", "side", "top", "other"]
        active_sides = list(label_sides) if label_sides else default_sides

        images_meta: List[Dict[str, Any]] = []
        all_detections: List[Dict[str, Any]] = []
        quality_reports: List[Dict[str, Any]] = []
        reference_objects: List[Dict[str, Any]] = []
        det_counter = 0

        engine = cls.get_engine()

        # ── Step 1: Try PaddleOCR on each image ──
        paddle_detections: List[Dict[str, Any]] = []

        for idx, img_path_str in enumerate(image_paths):
            img_path = Path(img_path_str)
            if not img_path.exists():
                logger.warning("OCRBridge: Image file does not exist: %s", img_path_str)
                continue

            img_id = f"img_{idx:03d}"
            side = active_sides[idx] if idx < len(active_sides) else "unspecified"

            cv_img = None
            img_width, img_height = 1920, 1080

            if has_cv2:
                cv_img = cv2.imread(str(img_path))
                if cv_img is not None:
                    img_height, img_width = cv_img.shape[:2]
            else:
                try:
                    from PIL import Image
                    with Image.open(img_path) as pil_img:
                        img_width, img_height = pil_img.size
                except Exception as img_err:
                    logger.warning("Failed to open image %s: %s", img_path, img_err)

            quality_dict = {
                "is_acceptable": True,
                "blur_score": 50.0,
                "blur_status": "OK",
                "issues": [],
            }
            if cv_img is not None:
                try:
                    from src.utils.image_quality import assess_image_quality
                    q_report = assess_image_quality(cv_img)
                    quality_dict = q_report.to_dict()
                except Exception:
                    pass
            quality_reports.append(quality_dict)

            images_meta.append({
                "image_id": img_id,
                "label_side": side,
                "width": img_width,
                "height": img_height,
                "filename": img_path.name,
                "quality": quality_dict,
            })

            # Try PaddleOCR
            if engine is not None and cv_img is not None:
                try:
                    raw_dets, _, _ = engine.detect_image(cv_img)
                    for raw_det in raw_dets:
                        text = str(raw_det.get("text", "")).strip()
                        if not text:
                            continue
                        det_counter += 1
                        conf = round(float(raw_det.get("confidence", 0.0)), 4)
                        raw_bbox = raw_det.get("bbox", {})
                        bbox = {
                            "x": int(raw_bbox.get("x", 0)),
                            "y": int(raw_bbox.get("y", 0)),
                            "width": int(raw_bbox.get("width", 0)),
                            "height": int(raw_bbox.get("height", 0)),
                        }
                        paddle_detections.append({
                            "detection_id": f"det_{det_counter:04d}",
                            "source_image_id": img_id,
                            "text": text,
                            "confidence": conf,
                            "bounding_box": bbox,
                        })
                    logger.debug("PaddleOCR: %d detections from %s", len(raw_dets), img_path.name)
                except Exception as det_err:
                    logger.error("PaddleOCR detect_image failed for %s: %s", img_path.name, det_err)

        # ── Step 2: If PaddleOCR returned 0 or unreadable/garbled detections, use Gemini Vision ──
        valid_paths = [p for p in image_paths if Path(p).exists()]
        if not _is_useful_ocr_result(paddle_detections) and valid_paths:
            logger.warning(
                "PaddleOCR produced %d detections which were empty or unreadable (e.g. GPU token corruption). "
                "Falling back to Gemini Vision OCR across %d image(s).",
                len(paddle_detections),
                len(valid_paths)
            )
            # Get Gemini API key from config if not provided
            _api_key = gemini_api_key
            if not _api_key:
                try:
                    from app.config import settings
                    _api_key = settings.GEMINI_API_KEY
                except Exception:
                    _api_key = os.getenv("GEMINI_API_KEY", "")

            vision_dets = _gemini_vision_ocr(valid_paths, _api_key, pkg_id, active_sides)
            all_detections = vision_dets
        else:
            all_detections = paddle_detections

        # ── Step 3: Detect Physical Reference Barcodes across all input images ──
        try:
            reference_objects = detect_reference_barcodes(
                valid_paths if valid_paths else image_paths,
                active_sides,
            )
            logger.info("OCRBridge: %d physical reference barcode(s) detected.", len(reference_objects))
        except Exception as ref_err:
            logger.warning("OCRBridge: reference barcode detection failed: %s", ref_err)
            reference_objects = []

        logger.info(
            "OCRBridge.run_ocr complete: %d total detections, %d reference object(s) (source: %s)",
            len(all_detections),
            len(reference_objects),
            "paddle" if paddle_detections else "gemini_vision"
        )

        return {
            "package_id": pkg_id,
            "images": images_meta,
            "reference_objects": reference_objects,
            "detections": all_detections,
            "quality_reports": quality_reports,
            "_ocr_source": "paddle" if paddle_detections else "gemini_vision",
        }

