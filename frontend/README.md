# ⚖️ MetroScan — AI-Powered Legal Metrology Compliance Checker

<p align="center">
  <img src="public/logo.webp" alt="State Emblem of India" width="90" />
</p>

<p align="center">
  <strong>Department of Legal Metrology</strong><br>
  <em>Ministry of Consumer Affairs, Food & Public Distribution — Government of India</em><br>
  <strong>Smart India Hackathon (SIH) 2026</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/SIH-2026-orange.svg" alt="SIH 2026" />
  <img src="https://img.shields.io/badge/Legal%20Metrology-PCR%202011-blue.svg" alt="Legal Metrology" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" alt="React 19" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?logo=vite" alt="Vite" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/License-Government%20of%20India-green.svg" alt="License" />
</p>

---

## 📌 Project Overview

**MetroScan** is an automated, AI-powered compliance auditing system developed for the **Smart India Hackathon (SIH) 2026**. 

The portal empowers enforcement officers, brand manufacturers, e-commerce platforms, and Indian consumers to instantly verify whether pre-packaged commodity labels strictly comply with the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011 (PCR 2011)**.

By leveraging multimodal edge optical character recognition (OCR) and generative AI, MetroScan detects non-compliant font heights, missing Unit Sale Prices (USP), absent manufacturer disclosures, misleading pack claims, and short-weight violations with **zero tolerance** in under 30 seconds.

---

## ✨ Key Features

### 1. 🔍 Automated Multi-Panel Label Inspection
- Simultaneous upload and live capture for **Front, Back, MRP Panel, and Side Panels**.
- Dual-engine OCR (PaddleOCR + EasyOCR) extracting text and numerals down to **0.5 mm** font heights.
- Multi-lingual OCR support across **English, Hindi (हिन्दी), and Marathi (मराठी)**.

### 2. 🤖 Gemini-Powered Statutory Structuring & Deterministic Rule Engine
- Generative AI structures chaotic, curved, and stylized package typography into the **10 Mandatory Declarations**.
- Enforces strict statutory requirements:
  1. **Rule 6(1)(a)** — Manufacturer, Packer & Importer Name & Complete Postal Address
  2. **Rule 6(1)(b)** — Generic & Common Commodity Name on Principal Display Panel (PDP)
  3. **Rule 6(1)(c)** — Net Quantity in Standard Metric Units (g, kg, ml, l)
  4. **Rule 6(1)(d)** — Month & Year of Manufacture, Packing, or Import
  5. **Rule 6(1)(e)** — Maximum Retail Price (MRP) with mandatory *"inclusive of all taxes"*
  6. **Rule 6(1)(f)** — Best Before / Expiry Date for consumables and perishables
  7. **Rule 6(1)(g)** — Consumer Care Cell (Name, Toll-Free Phone, Official Email)
  8. **Rule 6(1)(h)** — Country of Origin for imported goods & digital marketplaces
  9. **Rule 6(1)(i)** — Unit Sale Price (USP) per g/kg/ml/l adjacent to MRP
  10. **Rule 6(3)** — Minimum Numeral and Font Heights graduated by PDP surface area

### 3. 🗂️ Stacking Card Deck for Mandatory Declarations
- Framer-inspired physical card-overlap animation grouping the 10 statutory declarations into **5 paired thematic stages**.
- Staggered sticky top offsets and authentic top drop-shadows that slide and overlap as you scroll.
- High-contrast sovereign gradients (Sovereign Sapphire, Emerald Jade, Golden Amber, Crimson Ruby, and Cyber Steel).
- Built-in **5-Stage Navigator** for instant one-click smooth scrolling to any statutory provision.

### 4. 🧭 Expanding macOS Dock Workflow
- Dynamic horizontal accordion for the **How MetroScan Works** section.
- Hovering any stage expands it to prominent focus while smoothly compressing adjacent cards, mimicking the macOS Dock behavior.

### 5. 🧮 Legal Metrology Enforcement Workbench
- **Rule 6(3) Font Height Auditor**: Interactive PDP area slider with container toggle (Printed vs Blown/Moulded) computing statutory minimum font heights under Table 1 of the First Schedule.
- **Rule 6(1)(i) USP Generator**: Converts arbitrary MRP and net quantities into the legally formatted Unit Sale Price declaration.
- **Second Schedule MPE Auditor**: Verifies whether product net content deficiency falls within Maximum Permissible Error tolerances or warrants prosecution under Section 36(2).

### 6. 📊 Sector-Wise Compliance Breakdown (Master-Detail Dashboard)
- Interactive analytics dashboard across **9 regulated commodity sectors**:
  - Edible Oils & Vanaspati
  - Packaged Biscuits & Bakery
  - Cosmetics & Personal Care
  - Packaged Spices & Condiments
  - Dairy & Infant Nutrition
  - E-Commerce Imports
  - Packaged Drinking Water
  - Detergents & Cleaners
  - Cement & Building Pre-packs
- Features a prominent square hero card on the left with an 8-card responsive selector on the right.

### 7. 🗺️ National Inspection Heatmap
- Live geographic visualization using **Leaflet** showing state-wise and district-wise audit intensity, non-compliance hotspot clusters, and compounding notices.

### 8. 📄 Tamper-Evident Digital Compliance Certificates
- Generates official inspection certificates stamped with GPS coordinates, scan timestamp, detected violations, and cryptographic QR code validation.
- One-click PDF export via **jsPDF**.

### 9. 🤖 Inspector Piku — Animated Companion Mascot
- Physics-based floating mascot with interactive cursor-tracking eyes, ambient floating bounce, and real-time Legal Metrology tips.
- Non-intrusive cursor chase mode with offset flight coordinates and instant cancellation via `Escape` key.

---

## 🛠️ Tech Stack

### Frontend Core
- **Framework**: [React 19](https://react.dev/)
- **Bundler & Dev Server**: [Vite 8](https://vitejs.dev/)
- **Styling**: [Tailwind CSS 3.4](https://tailwindcss.com/) with custom Glassmorphism & Sovereign Theme Tokens
- **Animations**: [Framer Motion 13](https://www.framer.com/motion/)
- **Icons**: [Lucide React](https://lucide.dev/)

### Data & Visualization
- **Mapping**: [Leaflet 1.9](https://leafletjs.com/) & [React-Leaflet 5](https://react-leaflet.js.org/)
- **Charts**: [Recharts 3](https://recharts.org/)
- **PDF Generation**: [jsPDF 4](https://github.com/parallax/jsPDF)
- **Internationalization**: [i18next](https://www.i18next.com/) & [react-i18next](https://react.i18next.com/)
- **File Uploads**: [react-dropzone 20](https://react-dropzone.js.org/)

### Backend Integration
- **API**: FastAPI (Python)
- **AI / LLM**: Google Gemini 1.5 Flash / Pro Multimodal API
- **OCR Stack**: PaddleOCR / EasyOCR

---

## 🚀 Getting Started

Follow these steps to set up and run MetroScan locally.

### 1. Prerequisites

Make sure you have the following installed:
- [Node.js](https://nodejs.org/) (version `18.0` or higher recommended)
- [npm](https://www.npmjs.com/) (bundled with Node.js)
- [Git](https://git-scm.com/)

Verify installation:
```bash
node --version
npm --version
git --version
```

---

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/SIH-2026-MetroScan.git
   cd SIH-2026-MetroScan/metroscan-web
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

---

### 3. Running the Development Server

Launch the Vite local development server:
```bash
npm run dev
```

Open your browser and navigate to:
```
http://localhost:5173
```

---

### 4. Building for Production

To create an optimized, minified production build:
```bash
npm run build
```

To preview the production build locally:
```bash
npm run preview
```

---

## 📁 Directory Structure

```
metroscan-web/
├── public/
│   ├── logo.webp                 # State Emblem of India (Ashoka Stambha)
│   └── vite.svg
├── src/
│   ├── assets/                   # Static media and graphics
│   ├── components/
│   │   ├── audit/                # Package dropzone, OCR review, scorecards
│   │   ├── auth/                 # Animated login modal with mascot eye-tracking
│   │   ├── dashboard/            # KPI stats, Sector breakdown, India Heatmap
│   │   ├── declarations/         # Stacking 2-card deck for 10 Statutory Declarations
│   │   ├── footer/               # Sovereign footer with rotating 4-point star
│   │   ├── handbook/             # Legal Metrology Enforcement Workbench & Calculators
│   │   ├── header/               # SovereignHeader, Emblem, Language dropdown, Nav
│   │   ├── hero/                 # LiveProductScanner & interactive hero
│   │   ├── mascot/               # CuteFloatingMascot (Inspector Piku)
│   │   ├── navigation/           # AppleStyleDock
│   │   ├── registry/             # Audit history registry table
│   │   └── ui/                   # Shared UI primitives (InteractiveHoverButton, etc.)
│   ├── context/
│   │   ├── AuthContext.jsx       # Role-based authentication (Citizen / Inspector)
│   │   ├── LanguageContext.jsx   # Multilingual i18n context (EN / HI / MR)
│   │   └── ThemeContext.jsx      # Light / Dark mode theme toggle
│   ├── data/
│   │   └── mockScanData.js       # Statutory sample audits (Atta, Oil, Biscuits, etc.)
│   ├── App.jsx                   # Main layout and view assembler
│   ├── index.css                 # Custom glassmorphism, 3D card styles & animations
│   └── main.jsx                  # Application entry point
├── package.json
├── tailwind.config.js
└── vite.config.js
```

---

## ⚖️ Legal Disclaimer

This software is developed as part of the **Smart India Hackathon (SIH) 2026**. All statutory rules, penalties, font height minimums, and tolerance calculations are mapped directly to the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011**, as amended by the Ministry of Consumer Affairs, Food & Public Distribution, Government of India.

---

<p align="center">
  <strong>MetroScan</strong> — Protecting 1.4 Billion Consumers Through Automated Metrology Intelligence 🇮🇳
</p>
