"""
Field Validator: Semantic validation and Legal Metrology rule enforcement.
Checks date chronology, legal unit conformance, positive prices, and FSSAI structure.
"""
import re
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import config


def parse_date_obj(date_str: str) -> Optional[datetime]:
    """Parse date string into datetime object for chronological comparison."""
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%Y",
        "%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def validate_date(date_str: str) -> Tuple[bool, str, float, str]:
    """Validate extracted date string."""
    if not date_str:
        return False, "", 0.0, "Empty date"

    # Relative date like "2 years from mfg" is valid
    if "from mfg" in date_str.lower() or "months" in date_str.lower():
        return True, date_str, 0.0, "Valid relative shelf life"

    # Match numeric components
    match = re.search(r'(\d{1,2})[/.-](\d{1,2})?(?:[/.-](\d{2,4}))?', date_str)
    if not match:
        return False, date_str, -0.2, "Unrecognized date format"

    parsed = parse_date_obj(date_str)
    if parsed:
        year = parsed.year
        if not (2020 <= year <= 2040):
            return False, date_str, -0.3, f"Plausibility failed: year {year} out of expected range (2020-2040)"
        return True, date_str, 0.05, "Valid calendar date"

    return True, date_str, 0.0, "Date pattern recognized"


def validate_net_quantity(qty_str: str) -> Tuple[bool, str, float, str]:
    """Validate net quantity conforms to legal packaged commodity units."""
    if not qty_str:
        return False, "", 0.0, "Empty quantity"

    match = re.search(r'(\d+(?:\.\d+)?)\s*([A-Za-z.]+)', qty_str)
    if not match:
        return False, qty_str, -0.2, "No numeric amount found"

    val = float(match.group(1))
    unit = match.group(2).lower().replace(".", "")

    if val <= 0.0:
        return False, qty_str, -0.4, "Non-positive quantity"

    if unit in config.ALL_LEGAL_UNITS:
        return True, qty_str, 0.05, "Conforms to Legal Metrology packaged commodity units"

    return False, qty_str, -0.15, f"Unrecognized unit: {unit}"


def validate_mrp(mrp_str: str) -> Tuple[bool, str, float, str]:
    """Validate MRP is a plausible positive price."""
    if not mrp_str:
        return False, "", 0.0, "Empty MRP"

    clean_str = re.sub(r'[^\d.]', '', mrp_str)
    try:
        val = float(clean_str)
        if val <= 0.0:
            return False, mrp_str, -0.4, "Non-positive MRP"
        if val > 50000.0:
            return False, mrp_str, -0.2, "Plausibility failed: MRP unusually large"
        return True, clean_str, 0.05, "Plausible retail price"
    except ValueError:
        return False, mrp_str, -0.3, "Non-numeric MRP value"


def validate_license_number(lic_str: str) -> Tuple[bool, str, float, str]:
    """Validate FSSAI or AYUSH manufacturing license format."""
    if not lic_str:
        return False, "", 0.0, "Empty license number"

    digits = re.sub(r'\D', '', lic_str)
    if len(digits) == 14:
        if digits[0] in ['1', '2']:
            return True, digits, 0.08, "Valid 14-digit FSSAI registration structure"
        return True, digits, 0.0, "14-digit license number"

    # AYUSH / State license
    if "/" in lic_str and any(c.isalpha() for c in lic_str) and any(c.isdigit() for c in lic_str):
        return True, lic_str, 0.05, "Valid state AYUSH/manufacturing license pattern"

    return True, lic_str, 0.0, "Recognized license string"


def validate_cross_dates(mfg_date_str: Optional[str], exp_date_str: Optional[str]) -> Tuple[bool, str]:
    """Verify manufacturing date occurs on or before expiry date."""
    if not mfg_date_str or not exp_date_str:
        return True, "Single date present, cross-validation skipped"

    mfg_dt = parse_date_obj(mfg_date_str)
    exp_dt = parse_date_obj(exp_date_str)

    if mfg_dt and exp_dt:
        if mfg_dt > exp_dt:
            return False, f"Inconsistency: Mfg date ({mfg_date_str}) is AFTER Exp date ({exp_date_str})"
        return True, "Chronologically consistent"

    return True, "Date formats could not be strictly compared"
