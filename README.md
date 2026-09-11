# MetroScan — Automated Legal Metrology Compliance Verification System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF.svg)](https://vitejs.dev/)
[![Flutter 3.x](https://img.shields.io/badge/Flutter-3.x-02569B.svg)](https://flutter.dev/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-v2.9-red.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Gemini 3.6 Flash](https://img.shields.io/badge/Gemini-3.6%20Flash-orange.svg)](https://ai.google.dev/)

> **Smart India Hackathon (SIH 2026)**  
> An automated, end-to-end AI-powered compliance auditing system built for the **Department of Consumer Affairs (Legal Metrology Division)** to verify packaged commodity declarations against the statutory **Legal Metrology (Packaged Commodities) Rules, 2011**.

---

## 1. Executive Summary

Packaged commodities sold across India must strictly comply with mandatory statutory declarations under **The Legal Metrology Act, 2009** and **The Legal Metrology (Packaged Commodities) Rules, 2011**. Manual inspections by field enforcement officers are slow, subjective, and difficult to scale across millions of retail SKUs.

**MetroScan** solves this by providing:
1. **Multi-Panel Image Capture**: High-resolution multi-panel photo capture via Mobile App and Web Portal.
2. **High-Performance Optical Character Recognition**: Multi-stage OCR (GPU-accelerated PaddleOCR with fallback to Gemini Vision).
3. **Semantic Extraction**: Structured data normalization powered by Google Gemini 3.6 Flash.
4. **Deterministic Legal Engine**: 100% offline, explainable legal verification evaluating all 10 statutory rules with statutory citations and evidence traceability.
5. **Enforcement Dashboard & GIS Heatmap**: Real-time geo-tagged violation heatmaps, executive compliance metrics, digital PDF certificate generation, and automated notice dispatch.

---

## 2. End-to-End System Architecture

```
┌─────────────────────────┐       ┌─────────────────────────┐
│   Mobile App (Flutter)  │       │    Web Portal (React)   │
│  - Field Inspector Mode │       │  - Executive Dashboard  │
│  - Citizen Consumer Mode│       │  - Audit Studio & Maps  │
└────────────┬────────────┘       └────────────┬────────────┘
             │                                 │
             └────────────────┬────────────────┘
                              │ HTTP / REST API
                              ▼
                ┌───────────────────────────┐
                │   FastAPI Backend Server  │
                │     (0.0.0.0:8000)        │
                └─────────────┬─────────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  OCR-paddle  │    │ Gemini 3.6 Flash │    │  Deterministic Legal │
│  - GPU Infer │───>│   - Semantic     │───>│     Rule Engine      │
│  - Text BBox │    │     Extraction   │    │  - 10 Statutory Rules│
└──────────────┘    └──────────────────┘    └──────────┬───────────┘
                                                       │
                               ┌───────────────────────┴──────────────┐
                               ▼                                      ▼
                    ┌──────────────────────┐              ┌──────────────────────┐
                    │  Supabase (Postgres) │              │  Cloudinary Storage  │
                    │  - Audits & Scans    │              │  - Packaged Dossiers │
                    │  - User Auth & RBAC  │              │  - Generated PDFs    │
                    └──────────────────────┘              └──────────────────────┘
```

---

## 3. Statutory Rules Covered

MetroScan validates declarations deterministically against the **Legal Metrology (Packaged Commodities) Rules, 2011**:

| Rule Citation | Rule Name | Description & Verification Standard |
|---|---|---|
| **Rule 6(1)(a)** | Manufacturer / Packer / Importer | Verifies explicit name, full registered physical address, and pin code. |
| **Rule 6(1)(b)** | Generic / Common Commodity Name | Verifies generic or common commodity identity on the Principal Display Panel (PDP). |
| **Rule 6(1)(c)** | Net Quantity Declaration | Verifies valid metric SI units (`g`, `kg`, `ml`, `l`, `m`, `units`), flags illegal colloquialisms (`gms`, `kilos`, `lbs`). |
| **Rule 6(1)(d)** | Month & Year of Manufacture/Packing | Validates manufacturing, packing, or import date formatting (`MM/YYYY` or `Month YYYY`). |
| **Rule 6(1)(e)** | Maximum Retail Price (MRP) | Enforces mandatory `"inclusive of all taxes"` clause and standardized currency symbols (`₹` or `Rs.`). |
| **Rule 6(1)(f)** | Expiry / Best Before Date | Validates expiry date against manufacturing date and current date to prevent sale of expired goods. |
| **Rule 6(1)(g)** | Consumer Care Details | Verifies designated contact person, official email address, phone/toll-free number, and grievance address. |
| **Rule 6(1)(h)** | Country of Origin | Verifies country of origin for imported as well as domestic packaged goods. |
| **Rule 6(1)(i)** | Unit Sale Price (USP) | Enforces mandatory unit pricing for packages containing more than 1 kg or 1 litre. |
| **Rule 6(3)** | Minimum Font & Numeral Height | Verifies numeral and letter heights proportional to package area (with physical barcode scale reference). |

---

## 4. Repository Structure

```
SIH26034/
├── backend/                  # FastAPI Application & Legal Verification Core
│   ├── app/                  # Application modules (routes, services, dependencies)
│   │   ├── routes/           # API endpoints (scan, dashboard, auth)
│   │   ├── services/         # Business logic (auth, db, email, ocr, reports)
│   │   ├── config.py         # App configuration & environment loader
│   │   └── schemas.py        # Authoritative Pydantic API schemas
│   ├── legal_engine/         # Modular deterministic 10-rule legal validator
│   │   ├── rules/            # Individual statutory rule evaluators
│   │   └── engine.py         # Main legal engine orchestrator
│   ├── extractors/           # Gemini 3.6 Flash semantic extraction
│   ├── evaluation/           # Ground truth benchmark dataset & evaluators
│   ├── tests/                # Automated test suites
│   ├── scripts/              # Weight downloaders and database setup
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React 19 + Vite Web Application
│   ├── src/                  # Components, pages, context, and styles
│   │   ├── components/       # Audit studio, GIS heatmap, analytics, Poki assistant
│   │   ├── context/          # Authentication and theme state
│   │   └── App.jsx           # Main application shell
│   ├── package.json          # Node dependencies
│   ├── tailwind.config.js    # Tailwind styling system
│   └── vite.config.js        # Vite dev server & API proxy
│
├── mobile/                   # Flutter 3.x Cross-Platform Mobile App
│   ├── lib/                  # Dart source code
│   │   ├── core/             # Network constants and theme colors
│   │   ├── models/           # Dart data models matching backend schemas
│   │   ├── screens/          # Scanner, audit detail, login, and dashboard
│   │   └── widgets/          # Reusable UI widgets
│   └── pubspec.yaml          # Flutter dependencies
│
├── OCR-paddle/               # Modular PaddleOCR Inference Engine
│   ├── src/                  # PaddleOCR detector, recognizer, and preprocessors
│   └── config.py             # Model paths and hyperparameter settings
│
├── test_data/                # Sample Product Dossiers & Test Fixtures
│   ├── sampleinput.json      # Raw multi-detection OCR input
│   ├── sample_output.json    # Normalized semantic extraction contract
│   └── consolidated_data.json# Unified end-to-end audit dossier
│
├── docs/                     # Centralized Architectural Documentation
│   ├── MASTER_INTEGRATION_GUIDE.md
│   ├── METROSCAN_ARCHITECTURE_AND_WORKFLOW.md
│   ├── METROSCAN_COMPLETE_WORKFLOW.md
│   ├── SIH_COMPREHENSIVE_GUIDE.md
│   └── GPU_SETUP_GUIDE.txt
│
├── start_server.bat          # 1-Click Unified Development Launcher (Dynamic %~dp0)
├── test_api.py               # Live API integration test script
├── .env.example              # Monorepo environment variable template
├── .gitignore                # Production-grade Git ignore rules
└── LICENSE                   # MIT License
```

---

## 5. Prerequisites

- **Python 3.10+** (Miniconda / Anaconda recommended)
- **Node.js 18+** & **npm**
- **Flutter 3.x** & **Dart 3.x** (optional, for mobile app development)
- **Git**

---

## 6. Setup & Installation

### 1. Clone & Configure Environment
```bash
# Copy template environment file
copy .env.example backend\.env
```
Edit `backend/.env` and provide your API credentials (or leave `USE_MOCK=false` to test locally with live Gemini API keys).

### 2. Backend Installation
```bash
# Create and activate environment
conda create -n metroscan-gpu python=3.10 -y
conda activate metroscan-gpu

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Installation
```bash
cd frontend
npm install
cd ..
```

---

## 7. Running the Platform

### Option A: 1-Click Unified Launcher (Windows)
Double-click:
```text
start_server.bat
```
*Automatically frees ports, launches the FastAPI backend on `http://0.0.0.0:8000`, starts the Vite web portal on `http://localhost:5173`, and opens the browser.*

### Option B: Manual Service Startup

#### 1. Start Backend API Server
```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
- API Endpoint: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Start Web Portal
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
- Web Portal: `http://localhost:5173`

#### 3. Run Mobile App
```bash
cd mobile
flutter run
```
*Configure the Backend URL in the mobile app login settings to your laptop's IP (e.g. `http://192.168.x.x:8000`).*

---

## 8. Verification & Testing

### 1. Statutory Legal Engine Unit Tests
Runs 33 exhaustive test cases verifying all 10 statutory rules and margin-of-error tolerances:
```bash
python -m unittest backend/tests/test_legal_engine.py
```
*Expected: 33 tests passed in < 0.05 seconds.*

### 2. System Hardening & Security Test Suite
Tests time-aware expiry validation, email dispatch simulation, and dashboard RBAC:
```bash
python backend/test_hardening.py
```
*Expected: All modules and endpoints verified.*

### 3. Frontend Production Build
```bash
cd frontend
npm run build
```
*Expected: Clean Vite production bundle compiled.*

### 4. Offline Stage 5 Legal Validation
```bash
python backend/run_stage5.py
```
*Expected: Generates complete `compliance_result.json` evaluation dossier.*

---

## 9. Default Demo Credentials

For rapid evaluation and testing, the platform includes built-in role profiles:

| Role | Username / Email | Password | Access Rights |
|---|---|---|---|
| **Official Inspector** | `inspector@legalmetrology.gov.in` | `Inspector@123` | Full audit access, legal notices, PDF certificates, GIS heatmap |
| **Citizen Consumer** | `citizen@example.in` | `Citizen@123` | Personal scan history, verification scorecard |

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
