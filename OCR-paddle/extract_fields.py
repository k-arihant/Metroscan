"""
LEGACY / DEPRECATED PROTOTYPE SCRIPT
------------------------------------
This script was an early string-matching prototype on hardcoded OCR text.
Production execution uses:
    python main.py <image_path>
which runs the modular LabelCompliancePipeline in src.pipeline.
"""
import re

# OCR output from our current test
ocr_text = """
Net
200
ml
Lic. No. NDIAYU/6O
Batch No.
WD2606210
Mfg.
06/2026
Exp.
05/2029
Unit Sale Price
1.80
MRP
360.00
"""

# -------------------------
# Extract Net Quantity
# -------------------------

net_quantity = None

match = re.search(
    r'Net\s*(?:Quantity)?\s*(\d+(?:\.\d+)?)\s*(ml|g|kg|l|L)',
    ocr_text,
    re.IGNORECASE
)

if match:
    net_quantity = f"{match.group(1)} {match.group(2)}"


# -------------------------
# Extract dates
# -------------------------

dates = re.findall(
    r'\b(?:0[1-9]|1[0-2])/\d{4}\b',
    ocr_text
)

manufacturing_date = dates[0] if len(dates) >= 1 else None
expiry_date = dates[1] if len(dates) >= 2 else None


# -------------------------
# Extract Unit Sale Price
# -------------------------

unit_price = None

match = re.search(
    r'Unit\s*Sale\s*Price.*?(\d+\.\d{2})',
    ocr_text,
    re.IGNORECASE | re.DOTALL
)

if match:
    unit_price = match.group(1)


# -------------------------
# Extract MRP
# -------------------------

mrp = None

match = re.search(
    r'MRP.*?(\d+\.\d{2})',
    ocr_text,
    re.IGNORECASE | re.DOTALL
)

if match:
    mrp = match.group(1)


# -------------------------
# Display results
# -------------------------

print("\n========== EXTRACTED FIELDS ==========\n")

print("Net Quantity       :", net_quantity)
print("Manufacturing Date :", manufacturing_date)
print("Expiry Date        :", expiry_date)
print("Unit Sale Price    :", unit_price)
print("MRP                :", mrp)