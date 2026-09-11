"""
Field Classifier: Reusable negative classifiers and bounding box geometry auditor.
Identifies whether a candidate string resembles a date, phone number, FSSAI license,
batch code, net quantity, unit-sale-price, or barcode, preventing false field assignments.
"""
from typing import Tuple, List, Optional, Dict, Any
import re
import config
from src.utils.geometry import BoundingBox

# Date matching patterns
DATE_REGEX_COMPONENTS = [
    # Full DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    re.compile(r'\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])[/.-](20\d{2})\b'),
    # DD/MM/YY
    re.compile(r'\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])[/.-](\d{2})\b'),
    # MM/YYYY (e.g. 06/2026, 05/2029, 07/2026)
    re.compile(r'\b(0?[1-9]|1[0-2])[/.-](20\d{2})\b'),
    # MM/YY
    re.compile(r'\b(0?[1-9]|1[0-2])[/.-](\d{2})\b'),
    # With month name: e.g. 26.AUG.2026 or JAN 2027
    re.compile(r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[.\s-]*(20\d{2})\b', re.IGNORECASE),
    re.compile(r'\b(0?[1-9]|[12]\d|3[01])[.\s-]*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[.\s-]*(20\d{2})\b', re.IGNORECASE),
    # Relative: 24 months, 2 yrs from mfg
    re.compile(r'\b\d+\s*(?:months?|years?|yrs?)\b', re.IGNORECASE),
]

# 4-digit calendar year standalone: 2020 - 2035
YEAR_STANDALONE = re.compile(r'\b20[23]\d\b')

# 10-digit Indian phone, toll-free 1800, and landline numbers
PHONE_REGEX = re.compile(
    r'(?:(?:\+91[\s-]?)?(?:[6-9]\d{9}|\b\d{5}\s*\d{5}\b))|'
    r'(?:\b1800[\s-]?\d{2,4}[\s-]?\d{3,4}\b)|'
    r'(?:\b0\d{2,4}[-\s]?\d{6,8}\b)'
)

# 14-digit FSSAI licenses (starting with 1 or 2)
FSSAI_REGEX = re.compile(r'\b[12]\d{13}\b')

# AYUSH / State license numbers
AYUSH_REGEX = re.compile(r'\b[A-Za-z]{1,5}/[A-Za-z]{2,6}/\d{1,6}\b')
LIC_CODE_REGEX = re.compile(r'\b[A-Z]{2,6}[-\s]?\d{3,8}\b')

# Net quantity units
QUANTITY_UNIT_REGEX = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kgs|ml|m\.l\.|m\.l|l|ltr|litre|litres|liter|liters|mg|n|u|pcs?|units?)\b',
    re.IGNORECASE
)

# Unit Sale Price (USP)
USP_RATE_REGEX = re.compile(r'\b(\d+\.\d{2})\s*(?:/|per)\s*(?:g|gm|kg|ml|l|unit|n)\b', re.IGNORECASE)

# Standard EAN / UPC Barcode (12-13 digits)
BARCODE_REGEX = re.compile(r'\b\d{12,14}\b')

# Alphanumeric Batch / Machine Code
BATCH_CODE_REGEX = re.compile(r'\b[A-Za-z]{1,4}\d{3,8}[A-Za-z0-9]?\b|\b\d{2}[A-Za-z]\d{1,4}[A-Za-z0-9]{1,4}\b')


def looks_like_date(text: str) -> Tuple[bool, float, str]:
    """
    Check if text looks like a date or date component.
    Returns: (is_date, confidence, details)
    """
    clean = text.strip()
    if not clean:
        return False, 0.0, ""

    # Check date patterns
    for pat in DATE_REGEX_COMPONENTS:
        if pat.search(clean):
            return True, 0.95, "matches_calendar_date_pattern"

    # Standalone 4-digit year e.g. "2026", "2029"
    if YEAR_STANDALONE.search(clean):
        return True, 0.90, "matches_standalone_year"

    # Digits with slashes or dashes e.g. "07/26", "24/07"
    if re.search(r'\b\d{1,2}[/-]\d{1,2}\b', clean):
        return True, 0.85, "matches_partial_date_slash"

    # Isolated 2-digit month with zero-prefix in date context e.g. "07"
    # When text is strictly "01" through "12"
    if re.fullmatch(r'0[1-9]|1[0-2]', clean):
        return True, 0.70, "matches_zero_padded_month"

    return False, 0.0, ""


def looks_like_phone(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles a customer care or telephone number."""
    clean = text.strip()
    match = PHONE_REGEX.search(clean)
    if match:
        return True, 0.95, "matches_10_digit_phone"
    return False, 0.0, ""


def looks_like_fssai(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles a 14-digit FSSAI license."""
    clean = text.strip()
    # Strip any spaces or hyphens
    digits = re.sub(r'\D', '', clean)
    if len(digits) == 14 and digits.startswith(('1', '2')):
        return True, 0.98, "matches_14_digit_fssai"
    if FSSAI_REGEX.search(clean):
        return True, 0.95, "contains_14_digit_fssai"
    return False, 0.0, ""


def looks_like_license(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles state/AYUSH manufacturing license."""
    clean = text.strip()
    if AYUSH_REGEX.search(clean):
        return True, 0.95, "matches_ayush_license"
    if re.search(r'\b(?:lic|regn|licence)\b', clean, re.IGNORECASE):
        return True, 0.85, "contains_license_keyword"
    return False, 0.0, ""


def looks_like_batch(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles an alphanumeric batch code."""
    clean = text.strip().upper()
    # If the word is literally "BATCH" or "LOT"
    if clean in {"BATCH", "LOT", "BATCHNO", "LOTNO", "BATCHNUMMER"}:
        return True, 0.90, "batch_label_word"

    if BATCH_CODE_REGEX.search(clean):
        return True, 0.85, "matches_alphanumeric_batch_pattern"
    return False, 0.0, ""


def looks_like_quantity(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles net quantity with metric unit."""
    clean = text.strip()
    match = QUANTITY_UNIT_REGEX.search(clean)
    if match:
        val = float(match.group(1))
        unit = match.group(2).lower().replace(".", "")
        if unit in config.ALL_LEGAL_UNITS:
            return True, 0.95, f"matches_legal_quantity_{val}_{unit}"
        return True, 0.75, f"matches_quantity_{val}_{unit}"
    return False, 0.0, ""


def looks_like_unit_sale_price(text: str) -> Tuple[bool, float, str]:
    """Check if text resembles unit sale price fraction."""
    clean = text.strip()
    if USP_RATE_REGEX.search(clean):
        return True, 0.95, "matches_rate_per_unit"
    if re.search(r'\b(?:usp|unit\s*sale\s*price)\b', clean, re.IGNORECASE):
        return True, 0.90, "contains_usp_keyword"
    return False, 0.0, ""


def looks_like_barcode(text: str) -> Tuple[bool, float, str]:
    """Check if text is an unadorned EAN barcode."""
    clean = re.sub(r'\D', '', text.strip())
    if len(clean) in {12, 13, 14}:
        return True, 0.85, f"matches_{len(clean)}_digit_barcode"
    return False, 0.0, ""


def evaluate_bbox_quality(
    bbox: BoundingBox,
    image_shape: Tuple[int, int],
    text: str,
) -> Tuple[float, List[str]]:
    """
    Assess whether the bounding box geometry is sensible for the candidate text.
    Penalizes disproportionately large boxes (e.g. 1-character number spanning whole image width).
    Returns (penalty_score, diagnostic_notes).
    """
    img_h, img_w = image_shape[:2]
    if img_w <= 0 or img_h <= 0:
        return 0.0, []

    notes = []
    penalty = 0.0

    w_ratio = bbox.width / float(img_w)
    h_ratio = bbox.height / float(img_h)
    text_len = len(text.strip())

    # Case 1: Short text (<= 6 chars) spanning over 50% of the image width
    if text_len <= 6 and w_ratio > 0.50:
        penalty += config.PENALTY_HUGE_BBOX
        notes.append(f"Excessive bbox width ratio ({w_ratio:.2f}) for short text '{text}'")

    # Case 2: Short text spanning over 70% of image width (severe)
    elif text_len <= 4 and w_ratio > 0.70:
        penalty += (config.PENALTY_HUGE_BBOX * 1.5)
        notes.append(f"Severe image-spanning bbox width ({w_ratio:.2f}) for '{text}'")

    # Case 3: Disproportionate area ratio
    area_ratio = bbox.area / float(img_w * img_h)
    if text_len <= 5 and area_ratio > 0.20:
        penalty += -20.0
        notes.append(f"Excessive bbox area ratio ({area_ratio:.2f}) for short text")

    # Case 4: Compact, well-proportioned box bonus
    if 0.02 <= w_ratio <= 0.35 and 0.01 <= h_ratio <= 0.10:
        penalty += config.MRP_WEIGHT_COMPACT_BBOX
        notes.append("Compact, well-proportioned bounding box")

    return penalty, notes
