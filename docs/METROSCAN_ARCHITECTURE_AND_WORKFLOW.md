# MetroScan — Complete Tech Stack & Architectural Workflow Guide
### Smart India Hackathon 2026 | Problem Statement ID: 26034
**Team:** Xceptions  
**Title:** Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

---

## 1. Overview of the Solution

MetroScan replaces tedious 20–30 minute manual package inspections with a **30-second automated digital workflow**:
1. **For Legal Metrology Officers (Inspectors):** On-field automated multi-panel scanning, exact visual violation highlighting, GPS-locked evidence collection, deterministic fine calculation, and instant generation of official **Form 1 Legal Notices**.
2. **For Aware Citizens (Consumers):** Instant scam/misleading label detection, plain-language advisory reports, and one-tap grievance reporting.
3. **For State Regulators & Supervisors:** Centralized **GIS Heatmaps** mapping repeat offenders and district-level compliance trends.

---

## 2. Each and Every Tech Stack Component & Its Exact Role

Every technology in MetroScan was specifically chosen to solve a real-world inspection challenge. Here is the exact role of each component across the entire stack:

---

### A. Mobile Application (Field Officer & Citizen App)

* **Flutter (Dart):**
  * **Role:** Powers the cross-platform mobile application running on field inspectors' and citizens' Android devices.
  * **Why:** Provides native 60fps performance, high-speed camera rendering, and a single unified codebase for Android and iOS without managing two separate apps.
* **Geolocator:**
  * **Role:** Automatically locks the device's exact GPS latitude and longitude the moment a product is scanned at a retail store.
  * **Why:** Provides tamper-evident proof of location for court proceedings and feeds geo-coordinates into state-wide GIS violation heatmaps.
* **Image Calibration & Camera Capture:**
  * **Role:** Guides users to take clear, multi-angle photos (front, back, sides) and uses barcode/reference dimension scaling.
  * **Why:** Standardizes image inputs and provides pixel-to-millimeter calibration needed to accurately measure Rule 6(3) font heights.
* **Offline Sync & Local Storage:**
  * **Role:** Caches scans, product data, and pending reports locally on the phone when an inspector visits rural or basement markets with zero connectivity.
  * **Why:** Guarantees field officers can inspect products completely offline and automatically synchronizes data with Supabase once internet is restored.
* **Flutter PDFView (`flutter_pdfview`):**
  * **Role:** Directly renders generated Form 1 Legal Notices and Consumer Summaries inside the mobile app without forcing the user into third-party PDF apps.
* **Native File Sharing & Intents (`share_plus` / `path_provider`):**
  * **Role:** Interfaces with Android's native `FileProvider` and `ACTION_SEND` intents.
  * **Why:** Enables 1-tap **WhatsApp sharing with the real PDF file attached** to send directly to store owners, and pre-fills email notices with attached PDF documents.

---

### B. Web Application (Supervisory & Enforcement Portal)

* **React 18 / 19:**
  * **Role:** Powers the central administrative web portal used by senior directors, legal metrology controllers, and lab auditors.
  * **Why:** Fast, component-driven UI for handling complex state across large data tables and analytics dashboards.
* **Vite:**
  * **Role:** High-speed build tool and local development server.
  * **Why:** Delivers instant hot-module replacement (HMR) and optimized bundle generation for smooth browser performance.
* **Tailwind CSS:**
  * **Role:** Utility-first styling system across all web dashboards, cards, modals, and tables.
  * **Why:** Ensures clean, modern, responsive government-grade interface design with zero bloated CSS files.
* **Lucide React:**
  * **Role:** Consistent, accessible icon library for all UI actions, alert banners, and status badges.
* **React-Leaflet & OpenStreetMap:**
  * **Role:** Interactive Geographic Information System (GIS) mapping layer.
  * **Why:** Visualizes violation hotspots, pinpoints retail stores with frequent infractions, and tracks repeat offenders across districts without requiring expensive proprietary Google Maps API keys.
* **Recharts:**
  * **Role:** Data visualization engine rendering FMCG sector breakdowns, monthly compliance curves, and risk score distributions.
* **React-Dropzone:**
  * **Role:** Multi-file drag-and-drop file upload area allowing supervisors to batch-upload package photos for bulk automated compliance audits.

---

### C. Backend Engine (FastAPI & API Services)

* **FastAPI (Python 3.10+):**
  * **Role:** The core asynchronous REST API coordinating every request between frontend clients, cloud storage, computer vision, AI, and the database.
  * **Why:** Blazing fast execution (built on Starlette and uvloop), native support for asynchronous I/O, and direct native compatibility with Python's AI/CV libraries.
* **Uvicorn:**
  * **Role:** High-performance lightning-fast ASGI web server hosting the FastAPI application.
* **Pydantic v2:**
  * **Role:** Strict data validation and schema serialization.
  * **Why:** Guarantees that every incoming scan request and outgoing compliance payload strictly adheres to typed data contracts with zero runtime type errors.
* **JWT (JSON Web Tokens) & Google OAuth:**
  * **Role:** Secure authentication and role-based authorization.
  * **Why:** Authenticates field inspectors and citizens, protecting sensitive government enforcement records and ensuring verified user identity.

---

### D. AI & Computer Vision Pipeline

* **PaddleOCR (PP-OCRv4):**
  * **Role:** The "eyes" of MetroScan. Scans packaging surfaces to detect text characters and their precise spatial bounding-box coordinates `[x, y, w, h]`.
  * **Why:** Traditional OCR (like Tesseract) fails on shiny, curved, or multi-oriented packaging text. PaddleOCR is a modern deep-learning model specifically trained on curved, distorted, and arbitrary-oriented packaging fonts.
* **Computer Vision (OpenCV):**
  * **Role:** Image preprocessing layer that handles contrast normalization, glare reduction, edge detection, perspective correction, and visual bounding-box drawing over violations.
* **Google Gemini (1.5 / 2.0 Flash):**
  * **Role:** The "intelligent reader". Parses messy, unordered OCR text and extracts clean, structured packaging entities (Brand, MRP, Net Quantity, Unit, Mfg Date, Expiry, Manufacturer Address, Consumer Care).
  * **Why:** High-speed inference (under 1 second), low cost, and exceptional contextual understanding that distinguishes brand slogans from mandatory legal declarations.
* **Deterministic Statutory Validation Engine (Pure Python 10-Rule Engine):**
  * **Role:** The "strict judge". Evaluates statutory compliance with 100% mathematical certainty against **PCR 2011** Rules 6(1)(a-i), Rule 6(3), and Second Schedule Maximum Permissible Error (MPE).
  * **Why:** LLMs must **never** decide guilt or fines because they can hallucinate or fluctuate. A deterministic Python engine ensures zero hallucinations, complete auditability, and legal admissibility in court.

---

### E. Document Generation Engine

* **ReportLab (In-Memory PDF Engine):**
  * **Role:** Programmatically compiles and draws official multi-page PDF documents dynamically in server memory.
  * **Why:** Generates pixel-perfect, government-standard **Form 1 Legal Notices / Seizure Memos** (with national emblem headers, violation breakdown tables, and statutory sections) and simplified **Consumer Safety Advisories** in less than 1 second without needing a heavy browser.

---

### F. Shared Database & Cloud Storage

* **Cloudinary:**
  * **Role:** The media vault and tamper-evident cloud storage.
  * **What it stores:**
    1. Raw, full-resolution packaging photos uploaded from phones/web (`metroscan/raw_scans/{scan_id}/`).
    2. Annotated images with colored bounding boxes highlighting detected violations (`metroscan/annotated/{scan_id}/`).
    3. Generated official Form 1 and Consumer Advisory PDF documents (`metroscan/reports/report_{scan_id}.pdf`).
  * **Why:** Prevents filling up local server disk space, delivers media through global CDNs in milliseconds, and provides immutable URLs for legal evidence.
* **Supabase (PostgreSQL):**
  * **Role:** Central cloud relational database and identity management.
  * **What it stores:**
    1. User accounts, credentials, and role authorizations (`INSPECTOR` vs `CITIZEN`).
    2. Scan audit logs, timestamps, compliance scores (0–100%), and overall status (`COMPLIANT` / `NON_COMPLIANT`).
    3. Store names and locked GPS coordinates for GIS hotspot mapping.
    4. Exact violation records citing broken rules, expected vs actual values, and statutory penalty amounts under Section 36 of the Legal Metrology Act, 2009.
    5. FMCG product catalog, brand records, and barcode database.

---

## 3. End-to-End Workflow (How Data Flows Through the Stack)

Here is the exact step-by-step path taken from the moment a user scans a package to the generation of a legal notice:

### Step 1: Login & Session Initialization
* User opens Flutter Mobile or React Web.
* User logs in via email/password or Google OAuth.
* Request hits `POST /api/v1/auth/login` on FastAPI.
* FastAPI checks credentials with Supabase Auth, which verifies the password and checks the role (`INSPECTOR` or `CITIZEN`).
* Supabase returns a secure JWT token, which Flutter stores in secure device storage to persist the session.

### Step 2: Multi-Angle Capture & Geolocation Locking
* Field inspector captures 1 to 6 photos of the product (front panel, back label, MRP area, and side panels).
* The mobile app uses **Geolocator** to automatically lock the retail store's GPS coordinates.
* The app packages images, GPS coordinates, store name, and notes into a `multipart/form-data` payload and POSTs to `/api/v1/scan/analyze`.

### Step 3: Evidence Archival to Cloudinary
* FastAPI receives the image stream in server memory.
* Before processing, FastAPI uploads the raw photos to Cloudinary to preserve permanent, untampered evidence for legal enforcement. Cloudinary returns secure HTTPS CDN URLs.

### Step 4: Text Detection & Spatial Mapping (PaddleOCR + OpenCV)
* OpenCV preprocesses image contrast and orientation.
* PaddleOCR scans the image pixels, locating all text blocks and recording their exact spatial bounding box coordinates `[x, y, w, h]`.
* Output: A list of raw text detections with confidence scores.

### Step 5: Semantic Parsing & Structuring (Google Gemini)
* The raw text list is passed to Google Gemini Flash.
* Gemini filters out marketing noise and structures the text into a clean JSON object:
  * Manufacturer / Packer Name and Complete Address
  * Generic / Common Name of Commodity
  * Net Quantity and Unit (e.g., `200`, `g`)
  * Month and Year of Manufacture / Packing
  * Maximum Retail Price (MRP)
  * Best Before / Expiry Period
  * Consumer Care Phone Number and Email Address
  * Country of Origin
  * Unit Sale Price (USP per g/ml)

### Step 6: Deterministic Statutory Validation (Python Legal Engine)
* The structured JSON is passed to the Pure Python Legal Rules Engine.
* The engine evaluates the product against **PCR 2011**:
  * **Rule 6(1)(a):** Full manufacturer name and complete address present?
  * **Rule 6(1)(b):** Generic commodity name clearly declared?
  * **Rule 6(1)(c):** Net quantity in First Schedule legal units (`g`, `kg`, `ml`, `l`)? (Flags non-compliant units like `gms`).
  * **Rule 6(1)(d):** Month and Year of manufacture clearly formatted?
  * **Rule 6(1)(e):** MRP explicitly mentions *"inclusive of all taxes"*?
  * **Rule 6(1)(f):** Expiry or best-before period valid and not expired?
  * **Rule 6(1)(g):** Both telephone number and email provided for consumer complaints?
  * **Rule 6(1)(h):** Country of origin explicitly declared?
  * **Rule 6(1)(i):** Unit Sale Price declared for packages > 1 unit/kg/l?
  * **Rule 6(3):** Minimum numeral/font height verified against package area.
  * **Second Schedule (MPE):** Calculates Maximum Permissible Error tolerance (including 9% ratio tolerance for small sachets).
* The engine outputs an exact Compliance Score (0–100%), lists all specific violations, and calculates statutory penalty estimates under Section 36 of the Legal Metrology Act, 2009.

### Step 7: Permanent Storage in Supabase
* FastAPI saves the complete record in Supabase PostgreSQL:
  * Inserts the scan into `scans` table (UUID, score, status, store name, GPS lat/long, timestamp).
  * Inserts every detected infraction into `violations` table.
  * Links Cloudinary image URLs in `scan_images` table.

### Step 8: Dynamic Document Generation (ReportLab)
* FastAPI triggers ReportLab to generate an official PDF in server memory:
  * **For Officers:** Official **Form 1 Legal Notice / Seizure Certificate** citing the Legal Metrology Act 2009 sections, ready for judicial use.
  * **For Citizens:** Simplified **Consumer Safety Advisory Report**.
* The PDF is archived to Cloudinary and returned as a downloadable binary to the client.

### Step 9: Delivery, In-App Preview & Native Sharing
* **On Web:** Results update state-wide compliance heatmaps via React-Leaflet and OpenStreetMap.
* **On Mobile:**
  * Displays real-time compliance scorecard and exact violations.
  * Opens in-app PDF preview via `flutter_pdfview`.
  * User can download PDF to Android `Downloads/`.
  * User taps **WhatsApp**: Flutter uses `share_plus` and Android `FileProvider` to launch WhatsApp with the **actual PDF document attached** to send directly to store managers or team members.
  * User taps **Email**: Launches email client with pre-written legal subject line, violation details, and attached PDF.

---

## 4. Key Risks & How Our Tech Stack Solves Them

| Identified Risk in SIH 2026 | Technical Solution in MetroScan |
| :--- | :--- |
| **Poor image quality / curved packaging** | Guided multi-angle capture in Flutter + OpenCV contrast/orientation preprocessing + PaddleOCR deep-learning text detection. |
| **OCR character errors on stylized fonts** | Google Gemini Flash semantic normalization cleans up noisy OCR typos using contextual reasoning. |
| **AI hallucination & false legal penalties** | **Zero LLM legal decision-making.** The final compliance decision is strictly handled by a deterministic Python rule engine that applies statutory rules mathematically. |
| **Font size measurement inaccuracy** | Barcode reference scaling and image calibration convert camera pixel dimensions to exact millimeter font heights under Rule 6(3). |
| **Limited / zero internet connectivity in field** | Offline-first mobile architecture caches scans and image data locally in SQLite/device storage, automatically syncing with Supabase once online. |
| **Changing legal metrology amendments** | Modular, decoupled Python rules engine allows updating legal thresholds and rules without retraining or altering AI models. |
