"""
Field Candidate Representation.
Encapsulates an extracted semantic candidate, its associated spatial anchor,
detailed positive and negative evidence features, and multi-tier confidence levels.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.utils.geometry import BoundingBox


@dataclass
class FieldCandidate:
    field_name: str
    value: str
    raw_text: str
    anchor_text: Optional[str] = None
    anchor_bbox: Optional[BoundingBox] = None
    value_bbox: Optional[BoundingBox] = None
    source: str = "same_line"  # 'same_line', 'right_adjacent', 'below_adjacent', 'global_fallback', 'reocr'
    ocr_confidence: float = 0.0
    field_score: float = 0.0
    field_confidence: float = 0.0
    layout_confidence: Optional[float] = None
    final_confidence: float = 0.0
    status: str = "needs_recheck"  # 'verified', 'needs_recheck', 'rejected'
    evidence: Dict[str, Any] = field(default_factory=dict)
    decision_reasons: List[str] = field(default_factory=list)
    is_fallback: bool = False
    token_ref: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Produce structured dictionary for JSON audit trail."""
        res: Dict[str, Any] = {
            "value": self.value,
            "ocr_confidence": round(self.ocr_confidence, 2),
        }
        if self.layout_confidence is not None:
            res["layout_confidence"] = round(self.layout_confidence, 2)
        res["field_confidence"] = round(self.field_confidence, 2)
        res["final_confidence"] = round(self.final_confidence, 2)
        res["status"] = self.status
        res["source"] = self.source
        if self.anchor_text:
            res["anchor"] = self.anchor_text
        if self.anchor_bbox:
            res["anchor_bbox"] = self.anchor_bbox.to_dict()
        if self.value_bbox:
            res["bbox"] = self.value_bbox.to_dict()
        if self.evidence:
            res["evidence"] = self.evidence
        if self.decision_reasons:
            res["decision_reason"] = self.decision_reasons
        return res
