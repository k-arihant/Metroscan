"""
LEGACY / DEPRECATED PROTOTYPE SCRIPT
------------------------------------
This script was an early flat OCR test script on cropped images.
Production execution uses:
    python main.py <image_path>
which runs the modular LabelCompliancePipeline in src.pipeline.

Migration note: EasyOCR replaced with PaddleOCR 3.7.0 (GPU).
"""
import re
from paddleocr import PaddleOCR

# -----------------------------
# 1. RUN OCR
# -----------------------------

print("Starting PaddleOCR...")

ocr = PaddleOCR(lang='en', device='gpu:0')

image_path = "images/selected_region.jpg"

results = list(ocr.predict(image_path))

# Build flat list of (text, confidence) pairs from OCRResult dict-like objects
detections = []
for res_obj in results:
    if res_obj is None:
        continue
    texts = res_obj.get("rec_texts", [])
    scores = res_obj.get("rec_scores", [])
    for t, s in zip(texts, scores):
        if t.strip():
            detections.append((t.strip(), s))

# -----------------------------
# 2. COLLECT OCR TEXT
# -----------------------------

ocr_text = "\n".join(
    text
    for text, conf in detections
)

print("\n========== RAW OCR TEXT ==========\n")
print(ocr_text)


# -----------------------------
# 3. EXTRACT NET QUANTITY
# -----------------------------

net_quantity = None

match = re.search(
    r'Net.*?(\d+(?:\.\d+)?)\s*(ml|g|kg|l)',
    ocr_text,
    re.IGNORECASE | re.DOTALL
)

if match:
    net_quantity = f"{match.group(1)} {match.group(2)}"


# -----------------------------
# 4. EXTRACT DATES
# -----------------------------

dates = re.findall(
    r'\b(?:0[1-9]|1[0-2])/\d{4}\b',
    ocr_text
)

manufacturing_date = dates[0] if len(dates) >= 1 else None
expiry_date = dates[1] if len(dates) >= 2 else None


# -----------------------------
# 5. EXTRACT UNIT SALE PRICE
# -----------------------------

unit_price = None

match = re.search(
    r'Unit\s*Sale\s*Price.*?(\d+\.\d{2})',
    ocr_text,
    re.IGNORECASE | re.DOTALL
)

if match:
    unit_price = match.group(1)


# -----------------------------
# 6. EXTRACT MRP
# -----------------------------

mrp = None

match = re.search(
    r'MRP.*?(\d+\.\d{2})',
    ocr_text,
    re.IGNORECASE | re.DOTALL
)

if match:
    mrp = match.group(1)


# -----------------------------
# 7. DISPLAY RESULTS
# -----------------------------

print("\n========== EXTRACTED FIELDS ==========\n")

print("Net Quantity       :", net_quantity)
print("Manufacturing Date :", manufacturing_date)
print("Expiry Date        :", expiry_date)
print("Unit Sale Price    :", unit_price)
print("MRP                :", mrp)