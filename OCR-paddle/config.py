"""
Central Configuration for Food/Product Label Compliance OCR Pipeline.
Houses paths, quality thresholds, confidence brackets, legal units, and engine defaults.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

# Base directories
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
DEBUG_DIR = BASE_DIR / "debug"
OUTPUT_DIR = BASE_DIR / "output"

# PaddleOCR Engine Configuration (PaddleOCR 3.7.0 / PaddlePaddle GPU 3.3.1)
# The OCREngineManager singleton is initialized ONCE using these values.
PADDLE_LANG = 'en'
PADDLE_DEVICE = 'gpu:0'  # RTX 3050 Laptop GPU (CUDA 12.6, Compute 8.9)


# Image Quality Assessment Thresholds
BLUR_THRESHOLD_SEVERE = 5.0        # Laplacian variance below this is unreadable blur
BLUR_THRESHOLD_MODERATE = 35.0     # May benefit from sharpening/warning
MIN_IMAGE_DIMENSION = 300          # Minimum width or height for label processing
MIN_MEAN_BRIGHTNESS = 25.0         # Severe underexposure
MAX_MEAN_BRIGHTNESS = 245.0        # Severe overexposure / washout
LOW_CONTRAST_THRESHOLD = 30.0      # RMS contrast threshold

# Confidence Level Thresholds
CONFIDENCE_HIGH = 0.80
CONFIDENCE_MEDIUM = 0.55
CONFIDENCE_LOW = 0.35

# Legal Metrology Units (Solid, Liquid, Volume, Count)
LEGAL_MASS_UNITS: Set[str] = {
    "g", "gm", "gms", "gram", "grams", "kg", "kgs", "kilogram", "kilograms", "mg"
}
LEGAL_VOLUME_UNITS: Set[str] = {
    "ml", "m.l.", "m.l", "l", "ltr", "litre", "litres", "liter", "liters"
}
LEGAL_COUNT_UNITS: Set[str] = {
    "n", "u", "unit", "units", "piece", "pieces", "pc", "pcs", "refill", "capsules", "tablets"
}
ALL_LEGAL_UNITS: Set[str] = LEGAL_MASS_UNITS | LEGAL_VOLUME_UNITS | LEGAL_COUNT_UNITS

# Preprocessing Presets
PREPROCESSING_VARIANTS = [
    "standard",     # Grayscale + Bilateral Filter
    "clahe",        # Adaptive Histogram Equalization for colored/foil packaging
    "dot_matrix",   # Grayscale + Morphological closing for inkjet dots
    "sharpened",    # Unsharp mask + bicubic resize
]

# Field Names for Final Output Schema
RECOGNIZED_FIELDS = [
    "product_name",
    "net_quantity",
    "mrp",
    "unit_sale_price",
    "batch_number",
    "manufacturing_date",
    "expiry_date",
    "license_number",
    "manufacturer",
    "customer_care",
]

# -------------------------------------------------------------------------
# Candidate Scoring Weights (Positive Evidence)
# -------------------------------------------------------------------------
MRP_WEIGHT_KEYWORD_NEARBY = 30.0       # Explicit "MRP", "M.R.P.", "Max Retail Price" anchor nearby
MRP_WEIGHT_CURRENCY_NEARBY = 20.0      # Currency marker ("₹", "Rs.", "INR") nearby
MRP_WEIGHT_SAME_LINE = 20.0            # Candidate resides on exact same horizontal line as anchor
MRP_WEIGHT_SPATIAL_ADJACENT = 15.0     # Candidate directly right or below anchor within tight spatial radius
MRP_WEIGHT_OCR_CONSENSUS = 15.0        # Multiple OCR passes/engines extracted identical text
MRP_WEIGHT_PRICE_FORMAT = 10.0         # Standard numeric price format (e.g. DD.DD or whole integer)
MRP_WEIGHT_COMPACT_BBOX = 5.0          # Candidate has tight, compact bounding box appropriate for price

# -------------------------------------------------------------------------
# Candidate Scoring Penalties (Negative Evidence)
# -------------------------------------------------------------------------
PENALTY_LOOKS_LIKE_DATE = -35.0        # Resembles calendar date (e.g., DD/MM/YYYY, MM/YY, or month digit)
PENALTY_LOOKS_LIKE_PHONE = -40.0       # Resembles 10-digit mobile number or customer care string
PENALTY_LOOKS_LIKE_FSSAI = -40.0       # Resembles 14-digit FSSAI license or AYUSH pattern
PENALTY_LOOKS_LIKE_BATCH = -25.0       # Resembles alphanumeric lot/batch code
PENALTY_LOOKS_LIKE_QUANTITY = -25.0    # Resembles net quantity or count pattern
PENALTY_LOOKS_LIKE_USP = -25.0         # Resembles unit sale price or rate fraction
PENALTY_HUGE_BBOX = -30.0              # Disproportionate bounding box spanning large fraction of image width
PENALTY_GLOBAL_FALLBACK = -35.0        # Unanchored candidate discovered purely via global regex scan

# Spatial Distance Neighborhood Settings (relative to anchor font height)
SPATIAL_HORIZONTAL_MAX_RATIO = 8.0     # Max horizontal distance = anchor_height * 8.0
SPATIAL_VERTICAL_MAX_RATIO = 5.0       # Max vertical distance = anchor_height * 5.0

# -------------------------------------------------------------------------
# Decision Engine Thresholds
# -------------------------------------------------------------------------
DECISION_THRESHOLD_VERIFIED = 75.0     # Score >= 75: Candidate accepted as VERIFIED
DECISION_THRESHOLD_RECHECK = 45.0      # Score 45-74: Candidate marked as NEEDS_RECHECK
DECISION_AMBIGUITY_MARGIN = 10.0       # If top-2 candidates differ by < 10 points, mark as NEEDS_RECHECK

# -------------------------------------------------------------------------
# Targeted Re-OCR Configuration
# -------------------------------------------------------------------------
TARGETED_REOCR_ENABLED = True          # Perform high-resolution patch re-OCR for ambiguous/dot-matrix text
TARGETED_REOCR_MAX_ATTEMPTS = 3        # Max number of crops to re-OCR per image
TARGETED_REOCR_ALLOWLIST = "0123456789.₹/-RsMRP"

# -------------------------------------------------------------------------
# Stage 2: Dot-Matrix Text Recognition Configuration
# -------------------------------------------------------------------------
DOT_MATRIX_ENABLED = True
DOT_MATRIX_UPSCALE_FACTORS = [2.0, 3.0, 4.0]
DOT_MATRIX_KERNEL_SIZES = [
    (2, 1),
    (3, 1),
    (2, 2),
]
DOT_MATRIX_CLAHE_ENABLED = True
DOT_MATRIX_ADAPTIVE_THRESHOLD_ENABLED = True
DOT_MATRIX_MAX_REOCR_ATTEMPTS = 3

# Field-aware character allowlists for dot-matrix OCR
DOT_MATRIX_ALLOWLISTS = {
    "date": "0123456789/-.:",
    "mrp": "0123456789.,₹Rs/-",
    "batch": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-/.",
    "license": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/-.",
    "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/-.:,₹ ",
}

# -------------------------------------------------------------------------
# Stage 2: Layout-Aware Label/Value Association Configuration
# -------------------------------------------------------------------------
LAYOUT_DETECTION_ENABLED = True
ROW_VERTICAL_TOLERANCE_MULTIPLIER = 0.75
COLUMN_CLUSTER_TOLERANCE_MULTIPLIER = 2.5
LAYOUT_MIN_ROWS = 2
LAYOUT_MIN_COLUMN_CONFIDENCE = 0.65
LAYOUT_ASSIGNMENT_AMBIGUITY_MARGIN = 10.0
VALUE_REUSE_ALLOWED = False
DEBUG_VISUALIZATION_ENABLED = False

