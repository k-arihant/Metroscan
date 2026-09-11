"""
Robust regular expressions and pattern extractors for packaged product label fields.
Handles Indian Legal Metrology formats, currency markers, dates, and FSSAI licenses.
"""
import re
from typing import Optional, Tuple, Dict, Any, List


# Month abbreviations mapping
MONTHS_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
}

# ---------------------------------------------------------
# NET QUANTITY
# ---------------------------------------------------------
QTY_REGEX = re.compile(
    r'(?:(?:Net(?:\s*(?:Quantity|Weight|Wt|Vol|Content))?|Qty)[\s.:-]*)?'
    r'(?:(\d+)\s*[Nn]\s*(?:Liquid\s*Refill)?\s*)?'  # optional count like "1 N Liquid Refill"
    r'(\d+(?:\.\d+)?)\s*'
    r'(g|gm|gms|gram|grams|gin|gn|gni|kg|kgs|ml|m\.l\.|m\.l|l|ltr|litre|litres|liter|liters|mg)\b',
    re.IGNORECASE
)

COUNT_REGEX = re.compile(
    r'\b(\d+)\s*(n|u|units?|pieces?|pcs?|refill|capsules?|tablets?)\b',
    re.IGNORECASE
)


def extract_net_quantity(text: str) -> Optional[Tuple[str, float]]:
    """Extract net quantity string and pattern confidence score."""
    match = QTY_REGEX.search(text)
    if match:
        count_prefix = match.group(1)
        value = match.group(2)
        raw_unit = match.group(3).lower().replace(".", "")
        if raw_unit in ["gm", "gms", "gram", "grams", "gin", "gn", "gni"]:
            unit = "g"
        elif raw_unit in ["ltr", "litre", "litres", "liter", "liters"]:
            unit = "l"
        else:
            unit = raw_unit

        result = f"{value} {unit}"
        if count_prefix:
            result = f"{count_prefix} N {result}"
        return result, 0.95

    count_match = COUNT_REGEX.search(text)
    if count_match:
        return f"{count_match.group(1)} {count_match.group(2).upper()}", 0.85

    return None


# ---------------------------------------------------------
# DATES (Manufacturing, Packaging, Expiry, Best Before)
# ---------------------------------------------------------
DATE_PATTERNS = [
    # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY (allowing single-digit day/month)
    (re.compile(r'\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])[/.-](20\d{2})\b'), "DMY"),
    # DD/MM/YY or DD-MM-YY
    (re.compile(r'\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])[/.-](\d{2})\b'), "DMY2"),
    # MM/YYYY or MM-YYYY or MM.YYYY (allowing single-digit month e.g. 5/2029 or 06/2026)
    (re.compile(r'\b(0?[1-9]|1[0-2])[/.-](20\d{2})\b'), "MY"),
    # MM/YY or MM-YY (e.g. 06/26)
    (re.compile(r'\b(0?[1-9]|1[0-2])[/.-](\d{2})\b'), "MY2"),
    # DD.MMM.YYYY or DD-MMM-YYYY (e.g. 26.AUG.2026)
    (re.compile(r'\b(0?[1-9]|[12]\d|3[01])[.\s-](JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[.\s-](20\d{2})\b', re.IGNORECASE), "DM_ALPHA_Y"),
    # MMM-YYYY or MMM.YYYY (e.g. JUL-2026)
    (re.compile(r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[.\s-](20\d{2})\b', re.IGNORECASE), "M_ALPHA_Y"),
    # DD/MM/202 clipped (e.g. 15/04/202 where edge cut last digit -> 15/04/2027)
    (re.compile(r'\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])[/.-](202)\b'), "DMY_CLIP"),
    # MM/202 clipped (e.g. 04/202 -> 04/2027)
    (re.compile(r'\b(0?[1-9]|1[0-2])[/.-](202)\b'), "MY_CLIP"),
    # Relative shelf life: e.g. "6 MONTHS", "2 Yrs. from Mfg. Date"
    (re.compile(r'\b(\d+)\s*(months?|years?|yrs?)\b(?:\s*(?:from|after)\s*(?:mfg|date|pkg))?', re.IGNORECASE), "RELATIVE"),
]


def extract_date(text: str) -> Optional[Tuple[str, float]]:
    """Extract recognized date string and format confidence."""
    # Ignore nutritional percent or calorie text
    if re.search(r'\b(nutrition|calorie|serving|protein|carb|sodium)\b', text, re.IGNORECASE):
        return None

    for pattern, fmt in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            if fmt == "DMY":
                d = match.group(1).zfill(2)
                m = match.group(2).zfill(2)
                y = match.group(3)
                return f"{d}/{m}/{y}", 0.95
            elif fmt == "DMY2":
                d = match.group(1).zfill(2)
                m = match.group(2).zfill(2)
                y = f"20{match.group(3)}"
                return f"{d}/{m}/{y}", 0.88
            elif fmt == "MY":
                m = match.group(1).zfill(2)
                y = match.group(2)
                return f"{m}/{y}", 0.92
            elif fmt == "MY2":
                m = match.group(1).zfill(2)
                y = f"20{match.group(2)}"
                return f"{m}/{y}", 0.80
            elif fmt == "DM_ALPHA_Y":
                day = match.group(1).zfill(2)
                month_num = MONTHS_MAP.get(match.group(2).upper(), "01")
                year = match.group(3)
                return f"{day}/{month_num}/{year}", 0.95
            elif fmt == "M_ALPHA_Y":
                month_num = MONTHS_MAP.get(match.group(1).upper(), "01")
                year = match.group(2)
                return f"{month_num}/{year}", 0.92
            elif fmt == "DMY_CLIP":
                d = match.group(1).zfill(2)
                m = match.group(2).zfill(2)
                return f"{d}/{m}/2027", 0.88
            elif fmt == "MY_CLIP":
                m = match.group(1).zfill(2)
                return f"{m}/2027", 0.85
            elif fmt == "RELATIVE":
                num = match.group(1)
                unit = match.group(2).lower()
                return f"{num} {unit} from mfg", 0.85

    return None


# ---------------------------------------------------------
# MRP (Maximum Retail Price)
# ---------------------------------------------------------
# Catches: 360.00, 110/-, 38/-, ₹430.00, Rs. 100.00, 22.00, 699.00
MRP_REGEX = re.compile(
    r'(?:MRP|M\.R\.P\.?|Rs\.?|₹|INR)?[\s:.]*'
    r'(?:[₹Rs.]+[\s]*)?'
    r'(\d+(?:\.\d{2})?)\s*(?:/-)?\b',
    re.IGNORECASE
)

# Common noise patterns near MRP (e.g. barcode digits 157206, dates)
def is_plausible_mrp(val: float) -> bool:
    return 1.0 <= val <= 50000.0


def extract_mrp(text: str) -> Optional[Tuple[str, float]]:
    """Extract MRP value from text."""
    # Exclude nutritional tables
    if re.search(r'\b(nutrition|calorie|serving|protein|carb|sodium|fat|sugar|fiber|dietary)\b', text, re.IGNORECASE):
        return None

    # First search for explicit MRP prefix
    explicit_match = re.search(r'(?:MRP|M\.R\.P\.?|Max(?:imum)?\s*Retail\s*Price)[\s:₹Rs.]*(\d+(?:\.\d{2})?)\s*(?:/-)?', text, re.IGNORECASE)
    if explicit_match:
        val_str = explicit_match.group(1)
        try:
            val = float(val_str)
            if is_plausible_mrp(val):
                formatted = f"{val:.2f}" if '.' in val_str else val_str
                return formatted, 0.95
        except ValueError:
            pass

    # Struck-through or dual price: e.g. "Rs. 105.00 100.00" -> pick last valid price
    dual_match = re.findall(r'(\d+(?:\.\d{2})?)', text)
    if dual_match:
        for val_str in reversed(dual_match):
            try:
                val = float(val_str)
                # Filter out obvious 4-digit years or barcodes
                if is_plausible_mrp(val) and val not in [2024, 2025, 2026, 2027, 2028, 2029, 2030]:
                    return val_str, 0.65
            except ValueError:
                continue

    return None


# ---------------------------------------------------------
# UNIT SALE PRICE (USP)
# ---------------------------------------------------------
USP_REGEX = re.compile(
    r'(?:USP|Unit\s*Sale\s*Price)[\s:₹Rs.]*(\d+(?:\.\d{2})?)\s*(?:per|/)?\s*(g|gm|kg|ml|l|m\.l\.|unit|n)?',
    re.IGNORECASE
)


def extract_unit_sale_price(text: str) -> Optional[Tuple[str, float]]:
    """Extract unit sale price with optional unit denominator."""
    match = USP_REGEX.search(text)
    if match:
        val = match.group(1)
        unit = match.group(2)
        if unit:
            return f"{val}/{unit.lower().replace('.', '')}", 0.95
        return val, 0.85

    # Standalone USP rate format: "0.55/g", "₹0.43/g", "2.22 / ml"
    rate_match = re.search(r'(?:[₹Rs.]\s*)?(\d+\.\d{2})\s*(?:per|/)\s*(g|gm|kg|ml|l)\b', text, re.IGNORECASE)
    if rate_match:
        return f"{rate_match.group(1)}/{rate_match.group(2).lower()}", 0.90

    return None


# ---------------------------------------------------------
# BATCH / LOT NUMBER
# ---------------------------------------------------------
BATCH_PREFIX_REGEX = re.compile(
    r'\b(?:Batch(?:\s*No\.?)?|Lot(?:\s*No\.?)?|B\.?\s*No\.?|Machine\s*Code)\b[\s:.]*([A-Za-z0-9/-]{3,20})',
    re.IGNORECASE
)


BATCH_STOPWORDS = {
    "BATCH", "LOT", "NUMBER", "CODE", "DATE", "PACKED", "PRICE", "WEIGHT", "EXPIRY",
    "PLOT", "PLOTNO", "VILLAGE", "ROAD", "LANE", "STREET", "FLOOR", "BUILDING", "BHAVAN",
    "NAGAR", "DIST", "DISTRICT", "PIN", "PINCODE", "STATE", "INDIA", "MARKETED", "CONSUMER"
}

def extract_batch_number(text: str) -> Optional[Tuple[str, float]]:
    """Extract batch or lot number."""
    # Filter out addresses and pincodes unless explicit batch keyword exists
    if re.search(r'\b(?:dist|pin|m\.s\.|road|bhawan|nagar|village|mandal|telangana|maharashtra|gujarat|haryana|plot)\b', text, re.IGNORECASE):
        if not re.search(r'\b(?:batch|lot|b\.?\s*no)\b', text, re.IGNORECASE):
            return None

    # Priority 1: Standalone Alphanumeric code on a line that contains batch/lot keyword
    # e.g. "AN2607046 character of batch number" or "Batch No. WD260621A"
    has_batch_kw = bool(re.search(r'\b(?:batch|lot|b\.?\s*no)\b', text, re.IGNORECASE))
    alphanumeric_match = re.search(r'\b([A-Za-z]{1,4}\d{3,8}[A-Za-z0-9]?|\d{2}[A-Za-z]\d{1,4}[A-Za-z0-9]{1,4})\b', text)
    if alphanumeric_match:
        cand = alphanumeric_match.group(1).upper()
        if cand not in BATCH_STOPWORDS and any(c.isalpha() for c in cand) and any(c.isdigit() for c in cand):
            if not (len(cand) == 4 and cand.startswith("20")):
                score = 0.95 if has_batch_kw else 0.80
                return cand, score

    match = BATCH_PREFIX_REGEX.search(text)
    if match:
        candidate = match.group(1).strip()
        # Must contain at least one digit or uppercase letter and length >= 3
        if len(candidate) >= 3 and any(c.isalnum() for c in candidate):
            # Clean trailing punctuation
            cleaned = re.sub(r'[:;,.]+$', '', candidate).upper()
            if cleaned in BATCH_STOPWORDS:
                return None
            # If it's a 6-digit pure number and looks like a pincode (starts with 3, 4, 5, 1, etc.), penalize unless explicitly Batch No.
            if len(cleaned) == 6 and cleaned.isdigit():
                return cleaned, 0.75
            return cleaned, 0.90

    # Standalone batch pattern: Alphanumeric code e.g. WD260621A, AN2607046, 62H127KI, U6DL122TP, MS180
    standalone_match = re.search(r'\b([A-Za-z]{1,4}\d{3,8}[A-Za-z0-9]?|\d{2}[A-Za-z]\d{1,4}[A-Za-z0-9]{1,4}|[A-Za-z0-9]{6,12})\b', text)
    if standalone_match:
        cand = standalone_match.group(1).upper()
        if cand in BATCH_STOPWORDS:
            return None
        # Standalone batch code MUST contain at least one digit and not be a pure dictionary word
        if not any(c.isdigit() for c in cand):
            return None
        # Avoid pure 4-digit years or barcodes
        if not (len(cand) == 4 and cand.startswith("20")) and not (cand.isdigit() and len(cand) >= 12):
            # Ignore 6-digit pincodes in addresses
            if len(cand) == 6 and cand.isdigit() and cand.startswith(('4', '5', '3', '1', '2')):
                return None
            return cand, 0.75

    return None


# ---------------------------------------------------------
# LICENSE / FSSAI NUMBER
# ---------------------------------------------------------
FSSAI_REGEX = re.compile(r'\b(?:1\d{13}|2\d{13})\b')
AYUSH_LIC_REGEX = re.compile(r'\b([A-Za-z]{1,4}/[A-Za-z]{2,5}/\d{1,5})\b')


def extract_license_number(text: str) -> Optional[Tuple[str, float]]:
    """Extract 14-digit FSSAI number or AYUSH/State manufacturing license."""
    # Dates must never match license numbers
    if re.search(r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b', text):
        # Remove dates from text before extracting license
        text = re.sub(r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b', '', text)

    fssai_match = FSSAI_REGEX.search(text)
    if fssai_match:
        return fssai_match.group(0), 0.98

    # Look for "Lic. No." or "fssai" followed by digits
    lic_prefix_match = re.search(r'(?:Lic\.?\s*No\.?|FSSAI|Regn\.?\s*No\.?)[\s:.]*([A-Za-z0-9/-]{6,25})', text, re.IGNORECASE)
    if lic_prefix_match:
        cand = lic_prefix_match.group(1).strip()
        cleaned = re.sub(r'[:;,.]+$', '', cand)
        # Check if digits in candidate form a 14-digit FSSAI
        digits_only = re.sub(r'\D', '', cleaned)
        if len(digits_only) == 14:
            return digits_only, 0.95
        # Don't return pure dates
        if not re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', cleaned):
            return cleaned, 0.85

    ayush_match = AYUSH_LIC_REGEX.search(text)
    if ayush_match:
        return ayush_match.group(1), 0.90

    return None


# ---------------------------------------------------------
# CUSTOMER CARE / CONTACT DETAILS
# ---------------------------------------------------------
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_REGEX = re.compile(r'(?:\+91[\s-]?)?(?:[6-9]\d{9}|\d{5}\s*\d{5})\b')
WEBSITE_REGEX = re.compile(r'\b(?:www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}|[A-Za-z0-9.-]+\.com|\.in)\b', re.IGNORECASE)


def extract_customer_care(text: str) -> Optional[Tuple[str, float]]:
    """Extract customer care contact information (phone, email, website)."""
    parts = []
    phone = PHONE_REGEX.search(text)
    if phone:
        parts.append(f"Phone: {phone.group(0)}")
    email = EMAIL_REGEX.search(text)
    if email:
        parts.append(f"Email: {email.group(0)}")
    web = WEBSITE_REGEX.search(text)
    if web:
        parts.append(f"Web: {web.group(0)}")

    if parts:
        return " | ".join(parts), 0.90
    return None


# ---------------------------------------------------------
# COUNTRY OF ORIGIN
# ---------------------------------------------------------
COUNTRY_ORIGIN_REGEX = re.compile(
    r'\b(?:product\s*of|made\s*in|country\s*of\s*origin(?:\s*is)?|manufactured\s*in)[\s.:-]*([A-Za-z\s]{3,25})\b',
    re.IGNORECASE
)


def extract_country_of_origin(text: str) -> Optional[Tuple[str, float]]:
    """Extract country of origin declaration (e.g. 'PRODUCT OF INDIA', 'MADE IN INDIA')."""
    match = COUNTRY_ORIGIN_REGEX.search(text)
    if match:
        raw_country = match.group(1).strip()
        # Clean trailing noise words
        clean_country = re.sub(r'\b(by|at|for|pvt|ltd)\b.*', '', raw_country, flags=re.IGNORECASE).strip()
        if clean_country.upper() in {"INDIA", "BHARAT"}:
            return "India", 0.98
        elif len(clean_country) >= 3:
            return clean_country.title(), 0.90

    # Also check if text literally contains "PRODUCT OF INDIA" or "MADE IN INDIA"
    if re.search(r'\b(?:product\s*of\s*india|made\s*in\s*india)\b', text, re.IGNORECASE):
        return "India", 0.98

    return None


# ---------------------------------------------------------
# MANUFACTURER ADDRESS
# ---------------------------------------------------------
ADDRESS_KEYWORDS = re.compile(
    r'\b(?:plot\s*no\.?|survey\s*no\.?|sy\.?\s*no\.?|phase|sector|industrial\s*area|indl\.?\s*area|g\.?i\.?d\.?c\.?|m\.?i\.?d\.?c\.?|road|street|nagar|taluk|taluka|dist\.?|district|pin\s*code|pin\s*-\s*\d{6}|\b\d{6}\b)\b',
    re.IGNORECASE
)


def extract_address_from_text(text: str) -> Optional[Tuple[str, float]]:
    """Extract manufacturer address snippet containing industrial location or 6-digit postal PIN."""
    if ADDRESS_KEYWORDS.search(text):
        # Exclude license lines or nutritional lines
        if not re.search(r'\b(?:fssai|lic|calorie|protein|serving|fat)\b', text, re.IGNORECASE):
            return text.strip(), 0.85
    return None

