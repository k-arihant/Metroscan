"""
Centralized JSON Output Writer for PaddleOCR.
--------------------------------------------
Responsible for:
- Constructing the standardized raw OCR JSON schema
- Deterministic detection ID and image ID generation
- Validating schema compliance
- Persisting JSON files to output/<image_name>_ocr.json
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)


def build_ocr_json(
    image_name_or_path: Union[str, Path],
    width: int,
    height: int,
    detections: List[Dict[str, Any]],
    package_id: Optional[str] = None,
    label_side: str = "unknown",
) -> Dict[str, Any]:
    """
    Construct standardized OCR output dictionary according to required schema.

    Schema:
    {
      "package_id": "pkg_<stem>",
      "images": [
        {
          "image_id": "img_<stem>",
          "label_side": "unknown",
          "width": int,
          "height": int
        }
      ],
      "detections": [
        {
          "detection_id": "det_001",
          "source_image_id": "img_<stem>",
          "text": "...",
          "confidence": 0.9821,
          "bounding_box": {
            "x": 245,
            "y": 10,
            "width": 315,
            "height": 28
          }
        }, ...
      ]
    }
    """
    path_obj = Path(image_name_or_path)
    stem = path_obj.stem

    pkg_id = package_id if package_id else f"pkg_{stem}"
    img_id = f"img_{stem}"
    side = label_side if label_side else "unknown"

    formatted_detections: List[Dict[str, Any]] = []

    for idx, det in enumerate(detections):
        det_id = f"det_{idx + 1:03d}"
        text = det.get("text", "")
        conf = round(float(det.get("confidence", 0.0)), 4)
        raw_bbox = det.get("bbox", {})

        bbox = {
            "x": int(raw_bbox.get("x", 0)),
            "y": int(raw_bbox.get("y", 0)),
            "width": int(raw_bbox.get("width", 0)),
            "height": int(raw_bbox.get("height", 0)),
        }

        formatted_detections.append({
            "detection_id": det_id,
            "source_image_id": img_id,
            "text": text,
            "confidence": conf,
            "bounding_box": bbox,
        })

    return {
        "package_id": pkg_id,
        "images": [
            {
                "image_id": img_id,
                "label_side": side,
                "width": int(width),
                "height": int(height),
            }
        ],
        "detections": formatted_detections,
    }


def save_ocr_json(
    result: Dict[str, Any],
    image_name_or_path: Union[str, Path],
    output_dir: Union[str, Path] = "output",
) -> Path:
    """
    Save the standardized OCR JSON dictionary to disk.

    Output naming convention:
      <image_name>_ocr.json
    Saved inside output_dir (defaults to 'output/').

    Args:
        result: Formatted OCR JSON dictionary.
        image_name_or_path: Original image path or filename.
        output_dir: Output folder path (default: 'output').

    Returns:
        Path to the saved JSON file.
    """
    path_obj = Path(image_name_or_path)
    stem = path_obj.stem
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"{stem}_ocr.json"
    output_path = out_dir / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info("Saved OCR JSON to: %s", output_path)
    return output_path


def validate_ocr_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that an OCR dictionary adheres strictly to the required schema.

    Checks:
    - package_id exists and is non-empty str
    - images exists and contains required keys with numeric dimensions
    - detections is a list
    - each detection contains detection_id, source_image_id, text, confidence (0.0-1.0),
      and bounding_box with x, y, width, height numeric fields.
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return False, ["Root must be a dictionary"]

    # 1. package_id
    if "package_id" not in data or not isinstance(data["package_id"], str) or not data["package_id"].strip():
        errors.append("Missing or invalid 'package_id'")

    # 2. images
    if "images" not in data or not isinstance(data["images"], list) or len(data["images"]) == 0:
        errors.append("Missing or non-empty list 'images'")
    else:
        for idx, img in enumerate(data["images"]):
            if not isinstance(img, dict):
                errors.append(f"images[{idx}] must be a dict")
                continue
            for key in ["image_id", "label_side", "width", "height"]:
                if key not in img:
                    errors.append(f"images[{idx}] missing '{key}'")
            if "width" in img and not isinstance(img["width"], (int, float)):
                errors.append(f"images[{idx}].width must be numeric")
            if "height" in img and not isinstance(img["height"], (int, float)):
                errors.append(f"images[{idx}].height must be numeric")

    # 3. detections
    if "detections" not in data or not isinstance(data["detections"], list):
        errors.append("Missing or invalid list 'detections'")
    else:
        for idx, det in enumerate(data["detections"]):
            if not isinstance(det, dict):
                errors.append(f"detections[{idx}] must be a dict")
                continue
            for key in ["detection_id", "source_image_id", "text", "confidence", "bounding_box"]:
                if key not in det:
                    errors.append(f"detections[{idx}] missing '{key}'")

            if "confidence" in det:
                conf = det["confidence"]
                if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                    errors.append(f"detections[{idx}].confidence must be float between 0 and 1, got {conf}")

            if "text" in det and not isinstance(det["text"], str):
                errors.append(f"detections[{idx}].text must be a string")

            if "bounding_box" in det:
                bbox = det["bounding_box"]
                if not isinstance(bbox, dict):
                    errors.append(f"detections[{idx}].bounding_box must be a dict")
                else:
                    for bkey in ["x", "y", "width", "height"]:
                        if bkey not in bbox:
                            errors.append(f"detections[{idx}].bounding_box missing '{bkey}'")
                        elif not isinstance(bbox[bkey], (int, float)):
                            errors.append(f"detections[{idx}].bounding_box.{bkey} must be numeric")

    return len(errors) == 0, errors
