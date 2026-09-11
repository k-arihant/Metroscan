"""
Spatial geometry utilities for OCR bounding box manipulation, alignment, distance, and clustering.
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any
import math
import numpy as np


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @classmethod
    def from_polygon(cls, pts: Any) -> "BoundingBox":
        """Convert 4-point polygon coordinates (e.g. from PaddleOCR [[x,y],...]) to axis-aligned BoundingBox."""
        arr = np.array(pts)
        if arr.ndim == 2 and arr.shape[0] >= 4 and arr.shape[1] == 2:
            x_min = float(np.min(arr[:, 0]))
            x_max = float(np.max(arr[:, 0]))
            y_min = float(np.min(arr[:, 1]))
            y_max = float(np.max(arr[:, 1]))
            return cls(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)
        elif isinstance(pts, (list, tuple)) and len(pts) == 4:
            # Assume [x_min, y_min, x_max, y_max] or (x, y, w, h)
            return cls(x_min=float(pts[0]), y_min=float(pts[1]), x_max=float(pts[2]), y_max=float(pts[3]))
        raise ValueError(f"Unrecognized polygon format: {pts}")

    @classmethod
    def from_xywh(cls, x: float, y: float, w: float, h: float) -> "BoundingBox":
        return cls(x_min=float(x), y_min=float(y), x_max=float(x + w), y_max=float(y + h))

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2.0

    def to_xyxy(self) -> Tuple[int, int, int, int]:
        return int(round(self.x_min)), int(round(self.y_min)), int(round(self.x_max)), int(round(self.y_max))

    def to_dict(self) -> dict:
        return {
            "x_min": round(self.x_min, 1),
            "y_min": round(self.y_min, 1),
            "x_max": round(self.x_max, 1),
            "y_max": round(self.y_max, 1),
            "width": round(self.width, 1),
            "height": round(self.height, 1),
        }


def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes."""
    x_left = max(box1.x_min, box2.x_min)
    y_top = max(box1.y_min, box2.y_min)
    x_right = min(box1.x_max, box2.x_max)
    y_bottom = min(box1.y_max, box2.y_max)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = box1.area
    box2_area = box2.area
    union_area = box1_area + box2_area - intersection_area

    if union_area <= 0:
        return 0.0
    return intersection_area / union_area


def distance_between(box1: BoundingBox, box2: BoundingBox) -> float:
    """Euclidean distance between center points of two bounding boxes."""
    return math.sqrt((box1.center_x - box2.center_x) ** 2 + (box1.center_y - box2.center_y) ** 2)


def is_horizontally_aligned(box1: BoundingBox, box2: BoundingBox, max_v_overlap_ratio: float = 0.4) -> bool:
    """Check if two boxes are roughly on the same horizontal line."""
    avg_height = (box1.height + box2.height) / 2.0
    if avg_height == 0:
        return False
    v_diff = abs(box1.center_y - box2.center_y)
    return v_diff <= avg_height * max_v_overlap_ratio


def is_vertically_aligned(box1: BoundingBox, box2: BoundingBox, max_h_overlap_ratio: float = 0.5) -> bool:
    """Check if two boxes are roughly in the same vertical column."""
    avg_width = (box1.width + box2.width) / 2.0
    if avg_width == 0:
        return False
    h_diff = abs(box1.center_x - box2.center_x)
    return h_diff <= avg_width * max_h_overlap_ratio


def is_spatially_adjacent(
    key_box: BoundingBox,
    candidate_box: BoundingBox,
    direction: str = "right",
    max_gap_multiplier: float = 4.0,
) -> bool:
    """
    Check if candidate_box is positioned adjacent to key_box in the specified direction.
    direction: 'right' (same line, key to the left of candidate)
               'below' (next line down, column aligned)
    """
    if direction == "right":
        # Candidate must be to the right of key
        if candidate_box.x_min < key_box.x_min:
            return False
        # Center y difference must be within line tolerance
        if not is_horizontally_aligned(key_box, candidate_box, max_v_overlap_ratio=0.6):
            return False
        # Horizontal gap must be reasonable
        gap = candidate_box.x_min - key_box.x_max
        max_allowed_gap = max(key_box.height, 15.0) * max_gap_multiplier
        return -5.0 <= gap <= max_allowed_gap

    elif direction == "below":
        # Candidate must be below key
        if candidate_box.y_min < key_box.y_min:
            return False
        # Horizontal alignment should overlap or be column-aligned
        h_overlap = min(key_box.x_max, candidate_box.x_max) - max(key_box.x_min, candidate_box.x_min)
        if h_overlap < -key_box.width * 0.5:
            return False
        # Vertical gap between bottom of key and top of candidate
        gap = candidate_box.y_min - key_box.y_max
        max_allowed_gap = max(key_box.height, 15.0) * max_gap_multiplier
        return -5.0 <= gap <= max_allowed_gap

    return False
