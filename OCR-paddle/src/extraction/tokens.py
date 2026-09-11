"""
Canonical OCR Token and Token Store representation.
Preserves rich metadata per token: raw text, normalized text, bounding box,
OCR confidence, engine/variant consensus, and word/line relationships.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any
import re
import numpy as np

from src.ocr.engine_manager import OCRBox
from src.utils.geometry import (
    BoundingBox,
    calculate_iou,
    distance_between,
    is_horizontally_aligned,
    is_vertically_aligned,
)


@dataclass
class CanonicalToken:
    text: str
    normalized_text: str
    bbox: BoundingBox
    ocr_confidence: float
    engine: str = "ensemble"
    variant: str = "standard"
    token_type: str = "word"  # 'word' or 'line'
    child_tokens: List["CanonicalToken"] = field(default_factory=list)
    consensus_count: int = 1
    raw_box: Optional[OCRBox] = None

    @property
    def width(self) -> float:
        return self.bbox.width

    @property
    def height(self) -> float:
        return self.bbox.height

    @property
    def area(self) -> float:
        return self.bbox.area

    @property
    def confidence(self) -> float:
        return self.ocr_confidence

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "normalized_text": self.normalized_text,
            "bbox": self.bbox.to_dict(),
            "ocr_confidence": round(self.ocr_confidence, 3),
            "engine": self.engine,
            "variant": self.variant,
            "token_type": self.token_type,
            "consensus_count": self.consensus_count,
        }


class OCRTokenStore:
    """
    Indexed, queryable store of canonical OCR tokens for an image.
    Provides fast spatial retrieval: same-line, right-adjacent, below-adjacent,
    and neighborhood token searches.
    """

    def __init__(
        self,
        word_tokens: Optional[List[CanonicalToken]] = None,
        line_tokens: Optional[List[CanonicalToken]] = None,
        image_shape: Optional[Tuple[int, int]] = None,
    ):
        self.word_tokens: List[CanonicalToken] = word_tokens or []
        self.line_tokens: List[CanonicalToken] = line_tokens or []
        self.all_tokens: List[CanonicalToken] = self.word_tokens + self.line_tokens
        self.image_shape: Tuple[int, int] = image_shape or (1000, 1000)

    @classmethod
    def from_ocr_boxes(
        cls,
        words: List[OCRBox],
        lines: List[OCRBox],
        image_shape: Optional[Tuple[int, int]] = None,
    ) -> "OCRTokenStore":
        """Construct OCRTokenStore from raw OCRBox lists returned by multi-pass OCR."""
        # 1. Build word tokens
        c_words: List[CanonicalToken] = []
        for wb in words:
            norm = wb.text.strip().lower()
            if not norm:
                continue
            consensus = 1
            raw_det = getattr(wb, "raw_detection", None)
            if isinstance(raw_det, list):
                consensus = len(raw_det)

            c_words.append(
                CanonicalToken(
                    text=wb.text.strip(),
                    normalized_text=norm,
                    bbox=wb.bbox,
                    ocr_confidence=float(getattr(wb, "confidence", getattr(wb, "ocr_confidence", 0.9))),
                    engine=getattr(wb, "engine", "ensemble"),
                    variant=getattr(wb, "variant", "primary"),
                    token_type="word",
                    consensus_count=consensus,
                    raw_box=wb,
                )
            )

        # 2. Build line tokens with child word references
        c_lines: List[CanonicalToken] = []
        for lb in lines:
            norm_l = lb.text.strip().lower()
            if not norm_l:
                continue

            # Identify child word tokens inside this line
            children: List[CanonicalToken] = []
            raw_det_l = getattr(lb, "raw_detection", None)
            if isinstance(raw_det_l, list):
                # raw_detection contains the word OCRBoxes from cluster_into_lines
                raw_words = raw_det_l
                for rw in raw_words:
                    children.append(
                        CanonicalToken(
                            text=rw.text.strip(),
                            normalized_text=rw.text.strip().lower(),
                            bbox=rw.bbox,
                            ocr_confidence=float(getattr(rw, "confidence", getattr(rw, "ocr_confidence", 0.9))),
                            engine=getattr(rw, "engine", "ensemble"),
                            variant=getattr(rw, "variant", "primary"),
                            token_type="word",
                            raw_box=rw,
                        )
                    )
            else:
                # Fallback: spatial intersection with c_words
                for cw in c_words:
                    if (
                        cw.bbox.x_min >= lb.bbox.x_min - 5
                        and cw.bbox.x_max <= lb.bbox.x_max + 5
                        and cw.bbox.y_min >= lb.bbox.y_min - 5
                        and cw.bbox.y_max <= lb.bbox.y_max + 5
                    ):
                        children.append(cw)

            c_lines.append(
                CanonicalToken(
                    text=lb.text.strip(),
                    normalized_text=norm_l,
                    bbox=lb.bbox,
                    ocr_confidence=float(lb.confidence),
                    engine=lb.engine,
                    variant=lb.variant,
                    token_type="line",
                    child_tokens=children,
                    raw_box=lb,
                )
            )

        return cls(word_tokens=c_words, line_tokens=c_lines, image_shape=image_shape)

    def find_tokens_matching(
        self,
        regex: re.Pattern,
        in_lines: bool = True,
        in_words: bool = True,
    ) -> List[CanonicalToken]:
        """Find tokens matching a regex pattern."""
        pool: List[CanonicalToken] = []
        if in_lines:
            pool.extend(self.line_tokens)
        if in_words:
            pool.extend(self.word_tokens)

        matches = []
        for t in pool:
            if regex.search(t.text):
                matches.append(t)
        return matches

    def find_same_line_tokens(
        self,
        anchor_bbox: BoundingBox,
        max_v_diff_ratio: float = 0.5,
    ) -> List[CanonicalToken]:
        """Find word tokens sharing the same horizontal line band as the anchor."""
        results = []
        for wt in self.word_tokens:
            if is_horizontally_aligned(anchor_bbox, wt.bbox, max_v_overlap_ratio=max_v_diff_ratio):
                results.append(wt)
        # Sort left to right
        results.sort(key=lambda t: t.bbox.x_min)
        return results

    def find_tokens_right_of(
        self,
        anchor_bbox: BoundingBox,
        max_h_distance: float,
        max_v_diff_ratio: float = 0.6,
    ) -> List[Tuple[float, CanonicalToken]]:
        """
        Find word tokens strictly to the right of anchor within max_h_distance on same line.
        Returns list of (distance, token) sorted by distance ascending.
        """
        candidates = []
        for wt in self.word_tokens:
            # Candidate must start to the right of anchor start
            if wt.bbox.x_min < anchor_bbox.x_min:
                continue
            if not is_horizontally_aligned(anchor_bbox, wt.bbox, max_v_overlap_ratio=max_v_diff_ratio):
                continue

            # Gap between anchor right and token left
            gap = wt.bbox.x_min - anchor_bbox.x_max
            if -5.0 <= gap <= max_h_distance:
                dist = distance_between(anchor_bbox, wt.bbox)
                candidates.append((dist, wt))

        candidates.sort(key=lambda x: x[0])
        return candidates

    def find_tokens_below(
        self,
        anchor_bbox: BoundingBox,
        max_v_distance: float,
        max_h_overlap_ratio: float = 0.8,
    ) -> List[Tuple[float, CanonicalToken]]:
        """
        Find word/line tokens positioned below anchor within max_v_distance and column aligned.
        Returns list of (distance, token) sorted by vertical distance ascending.
        """
        candidates = []
        # Search word tokens first, then line tokens
        for t in self.word_tokens + self.line_tokens:
            if t.bbox.y_min < anchor_bbox.y_min:
                continue
            if not is_vertically_aligned(anchor_bbox, t.bbox, max_h_overlap_ratio=max_h_overlap_ratio):
                continue

            gap = t.bbox.y_min - anchor_bbox.y_max
            if -5.0 <= gap <= max_v_distance:
                dist = distance_between(anchor_bbox, t.bbox)
                candidates.append((dist, t))

        candidates.sort(key=lambda x: x[0])
        return candidates

    def find_tokens_above(
        self,
        anchor_bbox: BoundingBox,
        max_v_distance: float,
        max_h_overlap_ratio: float = 0.8,
    ) -> List[Tuple[float, CanonicalToken]]:
        """
        Find word/line tokens positioned above anchor within max_v_distance and column aligned.
        Returns list of (distance, token) sorted by vertical distance ascending.
        """
        candidates = []
        for t in self.word_tokens + self.line_tokens:
            if t.bbox.y_max > anchor_bbox.y_max:
                continue
            if not is_vertically_aligned(anchor_bbox, t.bbox, max_h_overlap_ratio=max_h_overlap_ratio):
                continue

            gap = anchor_bbox.y_min - t.bbox.y_max
            if -5.0 <= gap <= max_v_distance:
                dist = distance_between(anchor_bbox, t.bbox)
                candidates.append((dist, t))

        candidates.sort(key=lambda x: x[0])
        return candidates

    def find_nearest_tokens(
        self,
        anchor_bbox: BoundingBox,
        max_distance: float,
    ) -> List[Tuple[float, CanonicalToken]]:
        """Find all word tokens within euclidean max_distance from anchor."""
        candidates = []
        for wt in self.word_tokens:
            dist = distance_between(anchor_bbox, wt.bbox)
            if dist <= max_distance:
                candidates.append((dist, wt))
        candidates.sort(key=lambda x: x[0])
        return candidates
