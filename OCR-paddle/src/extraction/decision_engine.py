"""
Decision Engine: Multi-candidate arbitration, status assignment, ambiguity detection,
and confidence calibration.
"""
from typing import List, Tuple, Optional, Dict, Any
import config
from src.extraction.candidate import FieldCandidate


def arbitrate_candidates(
    field_name: str,
    candidates: List[FieldCandidate],
    threshold_verified: float = config.DECISION_THRESHOLD_VERIFIED,
    threshold_recheck: float = config.DECISION_THRESHOLD_RECHECK,
    ambiguity_margin: float = config.DECISION_AMBIGUITY_MARGIN,
) -> Tuple[Optional[FieldCandidate], List[Dict[str, Any]]]:
    """
    Arbitrate among candidate field values.
    Returns:
        (best_candidate_or_none, candidate_summary_list)
    """
    if not candidates:
        return None, []

    # Sort candidates by field score descending
    sorted_candidates = sorted(candidates, key=lambda c: c.field_score, reverse=True)

    candidate_summary = [
        {
            "value": c.value,
            "score": round(c.field_score, 1),
            "source": c.source,
            "status": c.status,
            "ocr_confidence": round(c.ocr_confidence, 2),
        }
        for c in sorted_candidates[:5]
    ]

    best = sorted_candidates[0]

    # Calculate normalized field confidence from field score
    # Score 100 -> ~0.98, Score 75 -> ~0.85, Score 50 -> ~0.60
    norm_field_conf = min(0.99, max(0.10, (best.field_score / 100.0) * 0.95 + 0.05))
    best.field_confidence = norm_field_conf

    # Final confidence blends field confidence (dominant: 70%) and OCR confidence (30%)
    best.final_confidence = (norm_field_conf * 0.70) + (best.ocr_confidence * 0.30)

    # 1. Check for immediate rejection (score too low or fatal negative penalties)
    if best.field_score < threshold_recheck:
        best.status = "rejected"
        best.decision_reasons.append(
            f"Candidate score ({best.field_score:.1f}) is below minimum acceptance threshold ({threshold_recheck:.1f})"
        )
        return None, candidate_summary

    # 2. Check for ambiguity between top 2 candidates
    if len(sorted_candidates) > 1:
        second = sorted_candidates[1]
        score_diff = best.field_score - second.field_score

        # If best has standard 2-decimal currency format and second is a non-decimal integer,
        # adjust margin to 5.0 points because standard currency format strongly dominates.
        effective_margin = ambiguity_margin
        if '.' in best.value and len(best.value.split('.')[1]) == 2 and '.' not in second.value:
            effective_margin = 5.0

        if score_diff < effective_margin and second.value != best.value:
            best.status = "needs_recheck"
            best.final_confidence = min(best.final_confidence, 0.65)
            best.decision_reasons.append(
                f"Ambiguity detected: competing candidate '{second.value}' scored {second.field_score:.1f} "
                f"(difference {score_diff:.1f} < margin {effective_margin})"
            )
            return best, candidate_summary

    # 3. Check for Verified vs Needs Recheck
    if best.field_score >= threshold_verified:
        # If candidate is solely from global fallback with no local anchor, do not verify blindly
        if best.is_fallback and not best.anchor_text:
            best.status = "needs_recheck"
            best.final_confidence = min(best.final_confidence, 0.60)
            best.decision_reasons.append("Unanchored global fallback candidate requires manual verification")
        else:
            best.status = "verified"
            best.decision_reasons.append(
                f"Candidate achieved high evidence score ({best.field_score:.1f} >= {threshold_verified:.1f})"
            )
    else:
        best.status = "needs_recheck"
        best.decision_reasons.append(
            f"Candidate evidence is moderate ({best.field_score:.1f}); flagged for review"
        )

    return best, candidate_summary
