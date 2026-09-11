# METROSCAN — COMPLETE SYSTEM WORKFLOW & ARCHITECTURE MANUAL
**Smart Legal Metrology Packaging Compliance & Enforcement System**
*Smart India Hackathon (SIH 2026) — Ministry of Consumer Affairs, Food & Public Distribution*

---

## 1. System Architecture Overview

MetroScan is an enterprise dual-role statutory compliance platform designed for the **Legal Metrology Division** and Indian citizens under the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATIONS                           │
├───────────────────────────────────┬─────────────────────────────────────┤
│      Flutter Android Mobile App   │       React / Web Portal (Gov)      │
│      (Inspector & Citizen Flow)   │       (Admin & State Regulator)     │
│   • 6-Panel Evidence Tray         │   • GIS Heatmap / Mandi Map         │
│   • Offline Audit Queue           │   • Enterprise Analytics            │
│   • Native PDF / WhatsApp / Mail  │   • Live Inspection Surveillance    │
└─────────────────┬─────────────────┴──────────────────┬──────────────────┘
                  │                                    │
                  ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CANONICAL FASTAPI BACKEND (:8000)                    │
├─────────────────────────────────────────────────────────────────────────┤
│  • Dual-Role JWT Authentication & RBAC (/api/v1/auth)                   │
│  • Multi-Panel Computer Vision & OCR Orchestrator (/api/v1/scan/analyze)│
│  • Statutory Legal Metrology 2011 Rule Evaluation Engine                │
│  • ReportLab Court-Admissible PDF Generator (/certificate.pdf, /report) │
│  • Dashboard KPIs & Aggregation Services (/api/v1/dashboard)            │
└─────────────────┬────────────────────────────────────┬──────────────────┘
                  │                                    │
                  ▼                                    ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│        AI / OCR SUBSYSTEMS        │ │      DATA PERSISTENCE LAYER       │
│  • PaddleOCR Text Engine          │ │  • Supabase / PostgreSQL          │
│  • Gemini Vision LLM Pipeline     │ │  • Profiles, Scans, Declarations  │
│  • Bounding Box Coordinate Mapper │ │  • Cloudinary Evidence Storage    │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 2. Dual-Role Workflows: Inspector vs. Citizen

MetroScan provides distinct user journeys tailored strictly to legal mandates:

### A. Legal Metrology Inspector Workflow (Official Enforcement)
1. **Official Authentication**:
   - Inspector authenticates with government credentials (`inspector@legalmetrology.gov.in`).
   - System validates role and issues a Bearer JWT session token containing Officer Name, Badge ID (`LM-DEL-8492`), and Enforcement Division.
2. **Field Dashboard**:
   - Real-time KPIs: Today's Audits, Violations Flagged, Compliance Rate, High-Risk Mandi Alerts.
   - Quick date filters (Today, This Week, This Month).
   - Dynamic Offline Audit Sync Banner displaying pending inspections.
3. **6-Panel Multi-Image Evidence Capture**:
   - 6 statutory slots in a scrollable Evidence Tray:
     - Slot 1: **Front Panel (PDP)** — Brand & Common Commodity Name
     - Slot 2: **Back / Info Panel** — Manufacturer / Packer Details & Address
     - Slot 3: **MRP & Net Qty Panel** — Maximum Retail Price (incl. of taxes), Net Content
     - Slot 4: **Side Panel 1** — Consumer Care email, phone & consumer contact
     - Slot 5: **Side Panel 2** — Barcode, Batch / Lot Number, statutory marks
     - Slot 6: **Base / Reference Panel** — Seal integrity or secondary declarations
   - Each slot supports live Camera capture or Gallery selection with real-time thumbnail preview and delete/retake controls.
4. **Automated Statutory Evaluation**:
   - Submits multi-panel images to `/api/v1/scan/analyze` with geo-coordinates and mandi/retail store name.
   - Evaluates all 10 statutory declarations under the 2011 Rules with millimeter font height measurement.
5. **Scorecard & Digital Enforcement Action**:
   - Renders the 10-Point Legal Metrology Scorecard.
   - Highlights non-compliant declarations (e.g. missing taxes clause, omitted USP, font height violations).
   - Allows inspector to tap and correct any OCR ambiguity before issuing memo.
6. **Form 1 Statutory Notice & Native Distribution**:
   - **Preview**: Displays the official Form 1 Notice styled with Government of India header, Ministry seal, tamper-proof SHA-256 hash, and digital badge.
   - **Download PDF**: Downloads the court-admissible PDF certificate directly to device storage (`/Download/MetroScan_Form1_Certificate_<id>.pdf`).
   - **WhatsApp Dispatch**: Opens Android native share sheet attaching the actual `.pdf` file with statutory legal notice text u/s 18 & 36.
   - **Email Notice Dispatch**: Dispatches the notice to manufacturer or retailer with the official `.pdf` attached.

### B. Citizen / Consumer Workflow (Public Protection)
1. **Consumer Portal**:
   - Consumer logs in or enters demo mode (`citizen@example.in`).
   - Personalized dashboard: "Namaste, Citizen!" with search bar for brand compliance history.
   - Legal Metrology Consumer Tips carousel explaining rights regarding MRP overcharging, net weight shortages, and dual MRP.
2. **Simplified Package Scan**:
   - One-tap "Scan Package Now" button.
   - Captures package panels (front, MRP, or nutritional/weight panels).
3. **Consumer Advisory Scorecard**:
   - Visual verdict badge: `COMPLIANT`, `WARNING`, or `NON_COMPLIANT`.
   - Consumer-friendly checklist of 10 key packaging parameters.
4. **Consumer Advisory Report (PDF) & Grievance Lodging**:
   - **Preview Report**: Displays the Consumer Packaging Advisory Report.
   - **National Consumer Helpline**: Prominent advisory referencing **Toll-Free 1915** and `consumerhelpline.gov.in`.
   - **Download / Share**: Citizen can download or share the Advisory Report via WhatsApp/Email to seek merchant resolution or lodge evidence.

---

## 3. Untethered Mobile Operation & Network Connectivity

When taking the physical smartphone into a supermarket basement or rural mandi with no cellular coverage, MetroScan operates completely untethered:

### A. Persistent Server Host Configuration
- Mobile is **NOT hardcoded** to `localhost` or `127.0.0.1`.
- Tapping the **Server** icon on the Login screen opens the runtime endpoint configuration dialog.
- Supported environments:
  - **Local Wi-Fi / LAN IP**: e.g., `http://192.168.1.15:8000` (Phone and laptop on the same Wi-Fi router).
  - **Cloud / Tunnel URL**: e.g., `https://metroscan.yourdomain.gov.in` or an HTTPS reverse proxy.
  - **USB Reverse Port Forward**: `http://127.0.0.1:8000` via `adb reverse tcp:8000 tcp:8000`.
- **Persistence**: Host settings are automatically saved to `${getApplicationDocumentsDirectory()}/custom_host.txt` and reloaded upon every app launch.

### B. Offline Evidence Collection Mode
- When an inspection is conducted with zero connectivity:
  - The network failure is gracefully intercepted.
  - The app displays an intuitive dialog: *"Save Inspection Offline?"*.
  - Tapping **Save Offline** safely copies all 1–6 captured high-resolution package photos into a protected permanent directory (`offline_scans/<scan_id>/`).
  - GPS coordinates, timestamp, store name, category, and panel mappings are written to an encrypted `meta.json`.
- **One-Tap Sync**:
  - Whenever the app detects pending offline scans, both the Inspector and Consumer dashboards render the **Offline Sync Banner**:
    ```
    [!] 2 Offline Audit(s) Pending
    Saved locally. Tap sync when online.          [ Sync ]
    ```
  - Tapping **Sync** sequentially uploads the stored evidence to `/api/v1/scan/analyze`, updates the official database, deletes the local offline files, and refreshes the dashboard KPIs.

---

## 4. 10-Point Legal Metrology (2011 Rules) Audit Matrix

Every scanned commodity is validated against the **Legal Metrology (Packaged Commodities) Rules, 2011**:

| Rule Citation | Statutory Declaration | Legal Standard | Compliance Check |
|---|---|---|---|
| **Rule 6(1)(a)** | Manufacturer / Packer Name & Address | Full name and complete physical address | Validated against entity register; flags missing pincode/street |
| **Rule 6(1)(b)** | Generic / Common Commodity Name | Generic name in prominent font | Checked against standard commodity taxonomy |
| **Rule 6(1)(c)** | Net Quantity in SI Units | Standard metric units (`g`, `kg`, `ml`, `l`, `m`) | SI abbreviation verified; flags invalid symbols (`gms`, `ml.`) |
| **Rule 6(1)(d)** | Month & Year of Mfg / Packing | Clear date of packaging/import | Validates presence of valid month and year |
| **Rule 6(1)(e)** | Maximum Retail Price (MRP) | "MRP ₹ ... (inclusive of all taxes)" | Mandates "(incl. of all taxes)" clause; flags omissions |
| **Rule 6(1)(f)** | Best Before / Expiry Date | Mandatory for perishable commodities | Expiry validity and shelf-life verified |
| **Rule 6(1)(g)** | Consumer Care Contact | Name, address, telephone & email | Validates presence of working email and phone |
| **Rule 6(1)(h)** | Country of Origin | Prominently stated for imported goods | Identifies domestic vs imported goods declaration |
| **Rule 6(1)(i)** | Unit Sale Price (USP) | Price per gram, kg, ml, or piece | Mandated since 2022 amendment for all packaged goods |
| **Rule 6(3)** | Minimum Font Height | Proportional to package net content | Measured in millimeters; verified against table heights |

---

## 5. PDF Generation & Native Android Sharing Engine

### Root Cause Analysis of Previous PDF Discrepancy
- **Root Cause 1**: The Flutter screen `pdf_preview_screen.dart` contained static placeholder text from initial prototyping ("Aashirvaad Whole Wheat Atta") rather than binding to `ScanResponse`.
- **Root Cause 2**: Backend `/certificate.pdf` requires an official Inspector JWT Bearer token. Previous mobile share routines invoked `/certificate.pdf` without authentication headers or role parameters, resulting in HTTP 403 Forbidden and falling back to a minimal 1-page blank PDF.

### Resolved Implementation
- **Dynamic Preview**: `PdfPreviewScreen` dynamically consumes `ScanResponse` via Riverpod (`scanStateProvider` and `scanDetailFutureProvider`), populating the exact scanned commodity name, brand, store name, geo-coordinates, timestamp, and 10 statutory declaration rows.
- **Role-Based Endpoints**:
  - Inspector: Hits `/api/v1/scan/{id}/certificate.pdf` with `Authorization: Bearer <token>` and `?token=<token>`.
  - Citizen: Hits `/api/v1/scan/{id}/report.pdf`.
- **Native File Sharing**:
  - `ShareService.shareViaWhatsApp` and `ShareService.sendViaEmail` download the authentic PDF bytes from the server, write them to a temporary file (`MetroScan_Notice_<id>.pdf`), and invoke Android's native `Share.shareXFiles([XFile(...)])`.
  - Attaches the actual `.pdf` file with correct MIME type `application/pdf` directly into WhatsApp and Gmail.

---

## 6. Strict Compliance Guarantees

1. **No Map in Mobile**:
   - The Flutter mobile application strictly contains **zero map widgets** (no Leaflet, no OpenStreetMap, no Google Maps).
   - Only lightweight GPS coordinate capture (`latitude`, `longitude`) is performed.
   - Comprehensive interactive GIS heatmaps remain exclusively in the Web Portal for state administrative surveillance.
2. **Web UI & Backend Safety**:
   - `WEB UI/` and `start_server.bat` remain completely pristine and unmodified.
   - Canonical FastAPI backend (`backend/`) remains the single source of truth.
3. **Data Preservation**:
   - Zero physical phone data destruction or formatting.
   - Supabase PostgreSQL schema and user tables are fully preserved.

---

## 7. Judge & Presentation Demonstration Guide

When demonstrating MetroScan to evaluation judges:

1. **Demonstrate Role Separation**:
   - Log in as Inspector: Show official badge ID, today's audit KPIs, and Form 1 generation.
   - Log in as Citizen: Show consumer advisory tips, 1915 helpline guidance, and consumer advisory reports.
2. **Demonstrate 6-Panel Capture**:
   - Open inspection camera, show 6 panel slots (PDP, Info, MRP, Sides, Base).
   - Tap "Sample" to demonstrate multi-panel image packing.
3. **Demonstrate Real Compliance Scorecard**:
   - Tap "Find Details" to run real compliance analysis.
   - Highlight the 10-point checklist with font height in millimeters and violation reasoning.
4. **Demonstrate PDF Generation & Native Sharing**:
   - Tap "View Official Notice" to preview the dynamically populated Form 1 Notice.
   - Tap "WhatsApp" or "Email": show Android's native share sheet with the attached `.pdf` document.
5. **Demonstrate Offline Readiness**:
   - Point out the persistent server configuration in Login.
   - Show how audits taken without internet are queued in the offline evidence tray and synchronized with one tap.
