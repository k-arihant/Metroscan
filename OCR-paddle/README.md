# Food & Product Label Compliance OCR System

A high-accuracy, modular OCR pipeline engineered to scan packaged food and commodity labels, automatically assess image quality, normalize orientations and skews, and extract structured compliance fields in accordance with **Indian Legal Metrology (Packaged Commodities)** standards.

Migrated from EasyOCR + Tesseract to **PaddleOCR on NVIDIA GPU** as the sole OCR engine.

---

## 1. Verified System Environment

| Component | Specification / Version |
|---|---|
| **OCR Engine** | **PaddleOCR 3.7.0** |
| **Deep Learning Framework** | **PaddlePaddle GPU 3.3.1** |
| **Execution Device** | `gpu:0` (NVIDIA GeForce RTX 3050 A Laptop GPU, 4GB VRAM) |
| **CUDA Runtime** | **CUDA 12.6** (Driver API: 13.1, GPU Compute Capability: 8.9) |
| **cuDNN Version** | **9.9.0** (`cudnn64_9.dll`) |
| **Python Environment** | **Python 3.12.10** (`.venv-gpu\Scripts\python.exe`) |

---

## 2. Architecture & Pipeline Flow

```
Input Image (File / Array)
       ↓
[Step 1: Image Quality Assessment]
  - Sharpness (Laplacian variance), mean brightness, RMS contrast
       ↓
[Step 2: Orientation & Deskew Normalization]
  - Reuses shared PaddleOCR singleton on downscaled preview (short-circuits at 0°)
  - Cardinal 90°/180°/270° alignment + Hough line angular deskew
       ↓
[Step 3: Adaptive Preprocessing Variants]
  - Standard (Bilateral), CLAHE (Contrast-enhanced), Dot-Matrix (Morphological closing)
       ↓
[Step 4: Multi-Pass PaddleOCR GPU Inference]
  - Pass 1: PaddleOCR standard variant (baseline detection & layout)
  - Pass 2: PaddleOCR CLAHE variant (contrast/foil packaging)
  - Pass 3: Dedicated Dot-Matrix specialist pass (inkjet stamps + character consensus)
       ↓
[Step 5: OCRBox Normalization & Consensus Aggregator]
  - Axis-aligned BoundingBox conversion from 4-point polygon coordinates
  - Positional IoU clustering, cross-pass confidence boosting, reading-order assembly
       ↓
[Step 6: Spatial Key-Value Extraction & Legal Metrology Validation]
  - 2D raycasting, column/row layout association, chronological date verification
       ↓
[Step 7: Standardized JSON Output & Rule 7 Compliance Evaluation]
  - Physical character height metrics, width-to-height aspect ratio validation
```

---

## 3. Directory Structure

```
OCR/
├── config.py                 # Central configurations (PADDLE_LANG='en', PADDLE_DEVICE='gpu:0')
├── requirements.txt          # Pinned project dependencies (paddleocr, paddlepaddle-gpu, opencv, pytest)
├── main.py                   # Production CLI entrypoint
├── ocr_extract.py            # Legacy standalone test script (migrated to PaddleOCR GPU)
│
├── src/
│   ├── pipeline.py           # End-to-end LabelCompliancePipeline coordinator
│   │
│   ├── utils/
│   │   ├── geometry.py       # BoundingBox dataclass, 4-point polygon adapter, 2D raycasting
│   │   └── image_quality.py  # Sharpness (Laplacian variance), exposure, contrast assessment
│   │
│   ├── preprocessing/
│   │   ├── orientation.py    # Shared singleton PaddleOCR text-scoring and Hough deskewing
│   │   └── pipeline.py       # Adaptive image variants (Standard, CLAHE, Dot-Matrix, Sharpened)
│   │
│   ├── ocr/
│   │   ├── engine_manager.py # Singleton OCREngineManager backing PaddleOCR GPU; OCRBox adapter
│   │   ├── multi_pass.py     # Multi-pass coordinator (Standard + CLAHE + Dot-Matrix)
│   │   ├── dot_matrix.py     # Inkjet/dot stamp detector, morphological bridging, consensus voting
│   │   └── aggregator.py     # Spatial clustering, confidence boosting, and line assembling
│   │
│   ├── extraction/
│   │   ├── patterns.py       # Strict regexes for dates, quantities, prices, FSSAI
│   │   ├── spatial_matcher.py# 2D Key-Value raycasting engine
│   │   ├── validator.py      # Legal Metrology rules and cross-date chronological validation
│   │   ├── layout_association.py # Multi-column / tabular label-to-value association
│   │   └── field_extractor.py# Field aggregation, confidence scoring, and JSON schema builder
│   │
│   ├── compliance/
│   │   └── rule_7.py         # Legal Metrology Rule 7 font height & width/height ratio validation
│   │
│   └── output/
│       ├── builder.py        # Standardized schema builder
│       └── schema.py         # Schema specification and validator
│
├── tests/
│   ├── ground_truth.json     # Ground truth labels for test dataset (t1-t11, test.jpeg)
│   ├── benchmark.py          # Automated accuracy & latency benchmarking harness
│   ├── test_extraction.py    # Unit tests for field extraction & chronological validation
│   ├── test_stage2.py        # Unit tests for layout association & dot-matrix voting
│   └── test_standardized_output.py # Unit tests for Rule 7 & schema conformance
│
├── tools/
│   └── diagnose_gpu.py       # Read-only GPU, CUDA 12.6, cuDNN, and tensor diagnostic tool
│
├── output/                   # Directory for generated compliance JSON files
└── images/                   # Sample test dataset (t1.jpeg - t11.jpeg, test.jpeg)
```

---

## 4. Usage Instructions

All commands must be executed using the project's GPU virtual environment:
`.\.venv-gpu\Scripts\python.exe`

### Run GPU Diagnostics
Verify CUDA 12.6, cuDNN, and GPU tensor execution:
```powershell
.\.venv-gpu\Scripts\python.exe tools\diagnose_gpu.py
```

### Run Full Test Suite
Run the 48-test automated pytest suite:
```powershell
.\.venv-gpu\Scripts\python.exe -m pytest tests/ -v --tb=short
```

### Process a Single Image
```powershell
.\.venv-gpu\Scripts\python.exe main.py images/test.jpeg
```

### Process Single Image and Save JSON
```powershell
.\.venv-gpu\Scripts\python.exe main.py images/test.jpeg --save-output output/
```

### Output Raw JSON to stdout
```powershell
.\.venv-gpu\Scripts\python.exe main.py images/test.jpeg --json
```

### Batch Directory Processing
Process an entire folder of label images and save standardized JSON outputs:
```powershell
.\.venv-gpu\Scripts\python.exe main.py --dir images/ --save-output output/
```

### Run Accuracy & Latency Benchmark
```powershell
.\.venv-gpu\Scripts\python.exe main.py --benchmark --limit 5
```

---

## 5. OCRBox Normalization & PaddleOCR 3.x Adapter

PaddleOCR 3.7.0 returns dict-like `OCRResult` structures per prediction:
- `rec_texts`: List of recognized string tokens.
- `rec_scores`: Recognition confidence scores (`0.0` to `1.0`).
- `rec_polys`: 4-point quadrilateral polygons `[[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ...]`.

`OCREngineManager._parse_ocr_result()` normalizes this output into the project's standard `OCRBox`:
```python
bbox = BoundingBox.from_polygon(poly)  # Computes min/max bounds in pixel coordinates
box = OCRBox(
    text=cleaned_text,
    bbox=bbox,
    confidence=float(score),
    engine="paddle",
    variant=variant,
    raw_detection={"poly": poly, "score": score},
)
```

### Character Allowlist Post-Processing
PaddleOCR 3.x does not provide inference-time character-level decoding constraints. To preserve the allowlist semantics originally used by EasyOCR and Tesseract in dot-matrix/stamped text passes, `_apply_allowlist_postprocess()` filters out disallowed characters post-recognition.

---

## 6. Troubleshooting & Gotchas

1. **Python Path Resolution**:
   - Always run with `.\.venv-gpu\Scripts\python.exe`.
   - Never invoke global Python (e.g. Python 3.14).
2. **First Inference Warm-up**:
   - On the very first inference call in a session, PaddlePaddle initializes the CUDA context and loads official models (`PP-OCRv6_medium_det`, `PP-OCRv6_medium_rec`, `PP-LCNet_x1_0_textline_ori`, `UVDoc`).
   - Subsequent calls in the same process reuse the singleton and are significantly faster.
3. **High-Resolution Images**:
   - For packaging photos over 4000px, PaddleOCR automatically scales down images to fit `max_side_limit=4000` for detection, preventing GPU VRAM allocation errors.
