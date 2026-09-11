"""
Legal Metrology (Packaged Commodities) Rules - Rule 7 Compliance Verification Module.

Deterministically evaluates:
1. Rule 7 Minimum Character Height Table based on Principal Display Panel (PDP) area:
   - Area <= 50 cm²: Normal 1.0 mm, Blown/Moulded 2.0 mm
   - 50 < Area <= 100 cm²: Normal 1.5 mm, Blown/Moulded 3.0 mm
   - 100 < Area <= 500 cm²: Normal 2.5 mm, Blown/Moulded 4.0 mm
   - 500 < Area <= 2500 cm²: Normal 4.0 mm, Blown/Moulded 6.0 mm
   - Area > 2500 cm²: Normal 6.0 mm, Blown/Moulded 6.0 mm
2. Rule 7(3) Character Width-to-Height Ratio:
   - Width / Height >= 1/3 (~0.333333)
   - Explicit exceptions for narrow characters: '1', 'i', 'I', 'l'.
3. Strict Regulatory Truth Rule:
   - If physical calibration (pixels_per_mm) or PDP area is unavailable,
     verification strictly returns 'UNABLE_TO_VERIFY'.
   - Physical millimetre values remain None / null. No fabrication.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List
import math


# Regulatory Table: (max_area_cm2, normal_min_mm, blown_min_mm)
# Note: Boundaries are strictly defined per Legal Metrology (Packaged Commodities) Rules, Rule 7, Table 1.
RULE_7_HEIGHT_TABLE: List[Tuple[float, float, float]] = [
    (50.0, 1.0, 2.0),
    (100.0, 1.5, 3.0),
    (500.0, 2.5, 4.0),
    (2500.0, 4.0, 6.0),
    (float('inf'), 6.0, 6.0),
]

MIN_WIDTH_HEIGHT_RATIO: float = 1.0 / 3.0  # 0.3333333333333333

# Rule 7(3) explicit narrow glyph exceptions
NARROW_CHARACTER_EXCEPTIONS: set = {'1', 'i', 'I', 'l', '|', '/', '\\'}

# Status enum constants
STATUS_COMPLIANT = "COMPLIANT"
STATUS_NON_COMPLIANT = "NON_COMPLIANT"
STATUS_UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"

VERIFICATION_VERIFIED = "VERIFIED"
VERIFICATION_UNABLE = "UNABLE_TO_VERIFY"


def get_required_character_height(
    pdp_area_cm2: float,
    blown_formed_moulded: bool = False,
) -> float:
    """
    Look up minimum required character height (in mm) based on PDP area.
    Boundaries:
      A <= 50 cm²        -> 1.0 mm (Normal) / 2.0 mm (Blown)
      50 < A <= 100 cm²  -> 1.5 mm (Normal) / 3.0 mm (Blown)
      100 < A <= 500 cm² -> 2.5 mm (Normal) / 4.0 mm (Blown)
      500 < A <= 2500 cm²-> 4.0 mm (Normal) / 6.0 mm (Blown)
      A > 2500 cm²       -> 6.0 mm (Normal) / 6.0 mm (Blown)
    """
    if pdp_area_cm2 <= 0:
        raise ValueError(f"Invalid PDP area: {pdp_area_cm2} cm² (must be positive)")

    for max_area, normal_min, blown_min in RULE_7_HEIGHT_TABLE:
        if pdp_area_cm2 <= max_area:
            return blown_min if blown_formed_moulded else normal_min

    return 6.0


def get_rule_7_threshold(pdp_area_cm2: float) -> Tuple[float, float]:
    """
    Convenience helper returning (normal_min_height_mm, blown_min_height_mm)
    for a given PDP area.
    """
    normal = get_required_character_height(pdp_area_cm2, blown_formed_moulded=False)
    blown = get_required_character_height(pdp_area_cm2, blown_formed_moulded=True)
    return normal, blown


@dataclass

class Rule7Evaluation:
    applicable: bool
    verification_status: str
    required_character_height_mm: Optional[float]
    measured_character_height_mm: Optional[float]
    height_status: str
    minimum_width_height_ratio: float
    measured_width_height_ratio: Optional[float]
    width_status: str
    overall_status: str
    confidence: float
    reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applicable": self.applicable,
            "verification_status": self.verification_status,
            "required_character_height_mm": round(self.required_character_height_mm, 2) if self.required_character_height_mm is not None else None,
            "measured_character_height_mm": round(self.measured_character_height_mm, 2) if self.measured_character_height_mm is not None else None,
            "height_status": self.height_status,
            "minimum_width_height_ratio": round(self.minimum_width_height_ratio, 6),
            "measured_width_height_ratio": round(self.measured_width_height_ratio, 4) if self.measured_width_height_ratio is not None else None,
            "width_status": self.width_status,
            "overall_status": self.overall_status,
            "confidence": round(self.confidence, 2),
            "reason": self.reason,
        }


def evaluate_rule_7_for_detection(
    text: str,
    character_height_px: Optional[float],
    minimum_character_width_px: Optional[float],
    width_height_ratio: Optional[float],
    measurement_available: bool,
    pixels_per_mm: Optional[float],
    pdp_area_cm2: Optional[float],
    blown_formed_moulded: bool = False,
    detection_type: str = "text",
) -> Rule7Evaluation:
    """
    Deterministically evaluate Legal Metrology Rule 7 for a single OCR detection.
    """
    # Exclude non-text/barcode graphics unless readable text
    if detection_type == "barcode":
        return Rule7Evaluation(
            applicable=False,
            verification_status=VERIFICATION_UNABLE,
            required_character_height_mm=None,
            measured_character_height_mm=None,
            height_status=STATUS_UNABLE_TO_VERIFY,
            minimum_width_height_ratio=MIN_WIDTH_HEIGHT_RATIO,
            measured_width_height_ratio=None,
            width_status=STATUS_UNABLE_TO_VERIFY,
            overall_status=STATUS_UNABLE_TO_VERIFY,
            confidence=0.0,
            reason="Rule 7 not applicable to barcode graphics.",
        )

    # Check availability of physical calibration and PDP area
    has_calibration = pixels_per_mm is not None and pixels_per_mm > 0
    has_pdp = pdp_area_cm2 is not None and pdp_area_cm2 > 0

    if not has_calibration or not has_pdp or not measurement_available or character_height_px is None:
        reasons = []
        if not has_calibration:
            reasons.append("Physical calibration (pixels_per_mm) is unavailable")
        if not has_pdp:
            reasons.append("Principal Display Panel (PDP) area is unavailable")
        if not measurement_available or character_height_px is None:
            reasons.append("Character glyph segmentation unavailable")

        reason_str = "; ".join(reasons) + "."
        return Rule7Evaluation(
            applicable=True,
            verification_status=VERIFICATION_UNABLE,
            required_character_height_mm=None,
            measured_character_height_mm=None,
            height_status=STATUS_UNABLE_TO_VERIFY,
            minimum_width_height_ratio=MIN_WIDTH_HEIGHT_RATIO,
            measured_width_height_ratio=width_height_ratio,
            width_status=STATUS_UNABLE_TO_VERIFY,
            overall_status=STATUS_UNABLE_TO_VERIFY,
            confidence=0.0,
            reason=reason_str,
        )

    # 1. Height Evaluation
    required_height_mm = get_required_character_height(pdp_area_cm2, blown_formed_moulded)
    measured_height_mm = character_height_px / pixels_per_mm

    # Height tolerance: must be >= required_height_mm (allowing floating-point epsilon 1e-4)
    height_compliant = measured_height_mm >= (required_height_mm - 1e-4)
    height_status = STATUS_COMPLIANT if height_compliant else STATUS_NON_COMPLIANT

    # 2. Width-to-Height Ratio Evaluation (Rule 7(3))
    # Minimum width / height >= 1/3 (0.333333)
    # Check if text contains only narrow exception characters
    clean_text = text.strip()
    is_all_narrow_exceptions = bool(clean_text) and all(c in NARROW_CHARACTER_EXCEPTIONS or c.isspace() for c in clean_text)

    actual_ratio = width_height_ratio
    if actual_ratio is None and minimum_character_width_px is not None and character_height_px > 0:
        actual_ratio = minimum_character_width_px / character_height_px

    if is_all_narrow_exceptions:
        # Exempt from width failure
        width_status = STATUS_COMPLIANT
    elif actual_ratio is not None:
        # Normal comparison: ratio >= 1/3
        if actual_ratio >= (MIN_WIDTH_HEIGHT_RATIO - 1e-4):
            width_status = STATUS_COMPLIANT
        else:
            width_status = STATUS_NON_COMPLIANT
    else:
        width_status = STATUS_UNABLE_TO_VERIFY

    # 3. Overall Evaluation
    if height_status == STATUS_COMPLIANT and width_status == STATUS_COMPLIANT:
        overall_status = STATUS_COMPLIANT
        reason = None
        conf = 0.92
    elif height_status == STATUS_NON_COMPLIANT or width_status == STATUS_NON_COMPLIANT:
        overall_status = STATUS_NON_COMPLIANT
        reasons = []
        if height_status == STATUS_NON_COMPLIANT:
            reasons.append(f"Measured height ({measured_height_mm:.2f} mm) < required ({required_height_mm:.2f} mm)")
        if width_status == STATUS_NON_COMPLIANT:
            reasons.append(f"Width/height ratio ({actual_ratio:.3f}) < required (0.333)")
        reason = "; ".join(reasons)
        conf = 0.90
    else:
        overall_status = STATUS_UNABLE_TO_VERIFY
        reason = "Width verification could not be conclusively determined."
        conf = 0.50

    return Rule7Evaluation(
        applicable=True,
        verification_status=VERIFICATION_VERIFIED,
        required_character_height_mm=required_height_mm,
        measured_character_height_mm=measured_height_mm,
        height_status=height_status,
        minimum_width_height_ratio=MIN_WIDTH_HEIGHT_RATIO,
        measured_width_height_ratio=actual_ratio,
        width_status=width_status,
        overall_status=overall_status,
        confidence=conf,
        reason=reason,
    )


def summarize_rule_7_compliance(evaluations: List[Rule7Evaluation]) -> Dict[str, Any]:
    """
    Roll up detection-level Rule 7 evaluations into a unified compliance summary.
    Summary is strictly derived from detection-level evaluations.
    """
    total = len(evaluations)
    verified = sum(1 for e in evaluations if e.verification_status == VERIFICATION_VERIFIED)
    compliant = sum(1 for e in evaluations if e.overall_status == STATUS_COMPLIANT)
    non_compliant = sum(1 for e in evaluations if e.overall_status == STATUS_NON_COMPLIANT)
    unable = sum(1 for e in evaluations if e.overall_status == STATUS_UNABLE_TO_VERIFY)

    if non_compliant > 0:
        overall_status = STATUS_NON_COMPLIANT
    elif compliant > 0 and unable == 0:
        overall_status = STATUS_COMPLIANT
    else:
        overall_status = STATUS_UNABLE_TO_VERIFY

    return {
        "status": overall_status,
        "verified": verified,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "unable_to_verify": unable,
        "detections_evaluated": total,
        "detections_compliant": compliant,
        "detections_non_compliant": non_compliant,
        "detections_unable_to_verify": unable,
    }

