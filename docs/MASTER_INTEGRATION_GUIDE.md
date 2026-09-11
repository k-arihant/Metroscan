# 🏛️ MetroScan Master Integration & Handover Guide (SIH 2026)
## The Complete Unified Playbook for Backend, Mobile (Flutter), Web (React), OCR & Legal Engine

---

## 1. System Architecture & Team Ownership

MetroScan is an end-to-end Legal Metrology inspection and compliance automation ecosystem designed for the **Legal Metrology (Packaged Commodities) Rules, 2011**.

```
                           ┌─────────────────────────────────────────┐
                           │            FIELD INSPECTION             │
                           │   Flutter Mobile App / React Web App    │
                           └────────────────────┬────────────────────┘
                                                │ (Multipart Images + GPS + JWT)
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FASTAPI BACKEND CORE (:8000)                                   │
│                                                                                                │
│  ┌──────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────────┐  │
│  │   Cloudinary Service │   │      AI Extractor         │   │      Deterministic Engine     │  │
│  │  (Evidence Imaging)  │   │   (PaddleOCR / Gemini)    │   │      (10 Statutory Rules)     │  │
│  └──────────────────────┘   └─────────────┬─────────────┘   └───────────────┬───────────────┘  │
│                                           │                                 │                  │
│                                           └───────────────┬─────────────────┘                  │
│                                                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │      ReportGeneratorService (Live IST Timestamp + Dynamic GPS + Form 1 Court PDF)        │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                           │                                    │
│  ┌──────────────────────────────┐                         ▼        ┌────────────────────────┐  │
│  │   Supabase PostgreSQL DB     │ ◄───────────────────────┴──────► │ Email Notice Dispatch  │  │
│  │ (Scans, Audit Logs, GIS Data)│                                  │ (Govt Authority Sender)│  │
│  └──────────────────────────────┘                                  └────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Team Role Ownership Matrix

| Role | Module / Directory | Primary Responsibility | Key Files |
|---|---|---|---|
| **Backend & Integration Lead** | `backend/app/` | API routing, DB sync, PDF generation, email dispatcher, auth | `routes/`, `services/`, `dependencies.py` |
| **OCR & Vision AI** | `backend/extractors/` & `weights/` | PaddleOCR text detection, bounding box extraction, Gemini semantic binding | `gemini_extractor.py`, `prompt.py`, `download_models.py` |
| **Rules & Legal Engine** | `backend/legal_engine/` | Deterministic statutory logic for 10 rules (6(1)(a) to 6(3)) | `engine.py`, `rules/rule_6_1_*.py` |
| **Mobile App (Flutter)** | `integration_kit/` | Mobile camera scanner, GPS auto-locking, offline-first caching | `metro_models.dart`, `api_service.dart` |
| **Web Portal (React)** | `web_integration_kit/` | React 18 + Vite, Tailwind CSS, React-Leaflet heatmap, Recharts analytics | `api.js` |

### Tech Stack (Confirmed & Updated)

| Layer | Technology |
|---|---|
| **Mobile Frontend** | Flutter (Dart) — Camera capture, GPS (geolocator), offline SQLite caching |
| **Web Frontend** | React 18/19 + Vite, Tailwind CSS, Lucide React, React-Leaflet (GIS map), Recharts (analytics), React-Dropzone |
| **Backend API** | FastAPI (Python 3.12+), Uvicorn, Pydantic v2 |
| **AI & Vision** | PaddleOCR (text detection & recognition) + Gemini 3.6 Flash (structured semantic extraction) |
| **PDF Generation** | ReportLab (in-memory vector Form 1 court PDF — zero internet required) |
| **Database** | Supabase (PostgreSQL) — scans, declarations, profiles, geo-coordinates |
| **Media Storage** | Cloudinary (permanent evidence image vault) |
| **Authentication** | Supabase Auth (JWT) with dual-role: `consumer` vs `inspector` / `admin` |

### Platform & Role Access Matrix

#### 📱 Mobile App (Flutter)
- **Users:** Citizens in retail stores & Inspectors on field raids.
- **Works offline:** Yes — photos, GPS coordinates, and scan data are cached locally on the device. Auto-syncs to cloud when internet resumes.
- **No heatmap, no analytics on mobile.**
- **Citizen can:** Scan packages, view compliance scorecard, download PDF report, receive PDF via email, see own scan history.
- **Inspector can:** All of the above + Form 1 Court Notice is officially stamped with their Badge ID, Officer Name, and Department.

#### 💻 Web Portal (React)
- **Users:** Ministry Directors, State Regulators, Inspectors at their desks, and Citizens on laptops.
- **NOT offline:** Requires internet — fetches live data from central database, renders GIS heatmap, pulls analytics.
- **Citizen can:** Upload package photos, view compliance scorecard, download PDF report, receive PDF via email, see own scan history. **Cannot** access heatmap, national analytics, or state-wide audit registry.
- **Inspector / Director / Regulator can:** All of the above + GIS Violation Heatmap, analytics charts (violation trends, category compliance), searchable state-wide Audit Registry, and official Form 1 Court Notices.

### Authentication & Role-Based Access Control

| Feature | Auth Requirement | Endpoint |
|---|---|---|
| **Sign Up** | None (public) | `POST /api/v1/auth/signup` with `role: "consumer"` or `"inspector"` (inspector also provides `badge_id`, `department`) |
| **Login** | None (public) | `POST /api/v1/auth/login` → returns JWT `access_token` and `role` |
| **Check Session** | Bearer Token | `GET /api/v1/auth/me` → returns role, name, badge, department |
| **Scan & Scorecard** | Optional (works without login) | `POST /api/v1/scan/analyze` |
| **Download PDF** | Optional | `GET /api/v1/scan/{id}/certificate.pdf` |
| **Email PDF** | Optional | `POST /api/v1/scan/{id}/email` |
| **Dashboard Stats** | **Inspector / Admin only** | `GET /api/v1/dashboard/stats` |
| **GIS Heatmap** | **Inspector / Admin only** | `GET /api/v1/dashboard/heatmap` |
| **Analytics Charts** | **Inspector / Admin only** | `GET /api/v1/dashboard/analytics` |
| **Audit Registry** | **Inspector / Admin only** | `GET /api/v1/dashboard/recent-scans` |

---

## 2. Environment Variables & Security Status

All credentials are saved in `backend/.env` and **strictly protected** by `.gitignore`:

```ini
USE_MOCK=true                                                     # Set false for live GPU/Cloud pipeline
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_public_key                        # Public anon key
SUPABASE_SERVICE_KEY=your_supabase_service_role_secret_key        # Private service key (Git-ignored)
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret                  # Private secret (Git-ignored)
GEMINI_API_KEY=your_gemini_api_key_here
```

> [!IMPORTANT]
> Both root `.gitignore` and `backend/.gitignore` are now active. Neither `.env` nor heavy model weights will ever be committed to Git.

---

## 3. Handling the 4 GB Model Weights Without Git Conflicts

Large neural network weights (`.pt`, `.bin`, `.onnx` > 100 MB) cannot be pushed to GitHub.

1. **Dedicated Weights Directory:**
   ```
   backend/weights/
   ├── .gitignore             # Hard-ignores all binaries (*.pt, *.bin, etc.)
   ├── yolov8_pdp.pt          # ~50-100 MB: Text panel detector
   ├── paddleocr_en/          # ~200 MB: Character recognition
   └── trocr_printed.bin      # ~1.2-2.5 GB: High-resolution printed text OCR
   ```
2. **Transferring Weights Between Teammates:**
   - **Local / Pen-drive:** Teammate drops weights directly into `backend/weights/`.
   - **Cloud Automated Download:** Run `python backend/scripts/download_models.py` to pull weights from cloud drive into `backend/weights/`.
3. **Memory Management (Singleton Startup):**
   Weights are loaded **once** at server startup into GPU/RAM, never re-instantiated on HTTP requests:
   ```python
   # Inside backend/app/services/core_engine.py
   WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "weights")
   # Global MODEL instance loaded on boot
   ```

---

## 4. Mobile App Integration Guide (Flutter)

### Step 1: Add Flutter Dependencies
In your Flutter project's `pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.2
  http_parser: ^4.0.2
  geolocator: ^12.0.0       # For live GPS coordinates
  open_filex: ^4.5.0        # To open downloaded PDF certificates
  path_provider: ^2.1.3     # Local device storage for certificates
```

### Step 2: Drop-in Ready Models & Services
Copy the files directly from `integration_kit/`:
```
lib/
├── models/
│   └── metro_models.dart   <-- from integration_kit/models/metro_models.dart
└── services/
    └── api_service.dart    <-- from integration_kit/services/api_service.dart
```

### Step 3: Configure Base URL
In `lib/main.dart` or during app initialization:
```dart
import 'package:your_app/services/api_service.dart';

void initMetroScan() {
  // Option A: Running in Chrome/Web:
  ApiService.setBaseUrl('http://localhost:8000/api/v1');

  // Option B: Running in Android Studio Emulator:
  // ApiService.setBaseUrl('http://10.0.2.2:8000/api/v1');

  // Option C: Physical Android/iOS Device (on same Wi-Fi as laptop):
  // ApiService.setBaseUrl('http://192.168.1.XX:8000/api/v1');
}
```

### Step 4: Complete Scan Submission Flow (Camera + GPS + Scorecard)
```dart
import 'dart:typed_data';
import 'package:image_picker/image_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:your_app/models/metro_models.dart';
import 'package:your_app/services/api_service.dart';

Future<ScanResponse?> executePackageAudit(List<XFile> images, String storeName) async {
  // 1. Fetch live GPS coordinates
  Position pos = await Geolocator.getCurrentPosition(
    desiredAccuracy: LocationAccuracy.high,
  );

  // 2. Read image bytes
  List<Uint8List> byteList = [];
  List<String> fileNames = [];
  for (var file in images) {
    byteList.add(await file.readAsBytes());
    fileNames.add(file.name);
  }

  // 3. Submit scan to backend
  ScanResponse response = await ApiService.submitScanBytes(
    imageBytesList: byteList,
    fileNames: fileNames,
    storeName: storeName,
    latitude: pos.latitude,
    longitude: pos.longitude,
  );

  return response;
}
```

### Step 5: Viewing & Downloading Official PDF Certificate
```dart
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import 'dart:io';

Future<void> downloadAndOpenCertificate(String scanId, String storeName, double lat, double lng) async {
  final url = Uri.parse(
    "http://localhost:8000/api/v1/scan/$scanId/certificate.pdf"
    "?store_name=${Uri.encodeComponent(storeName)}&latitude=$lat&longitude=$lng"
  );

  final res = await http.get(url);
  if (res.statusCode == 200) {
    final tempDir = await getTemporaryDirectory();
    final file = File("${tempDir.path}/MetroScan_Notice_$scanId.pdf");
    await file.writeAsBytes(res.bodyBytes);
    await OpenFilex.open(file.path);
  }
}
```

---

## 5. Web Portal Integration Guide (React)

### Step 1: Copy API Client
Copy `web_integration_kit/api.js` into `src/services/api.js`.

### Step 2: Connect React Component to Backend
```jsx
import React, { useState } from 'react';
import { MetroApi } from '../services/api';

export default function PackageAuditForm() {
  const [images, setImages] = useState([]);
  const [storeName, setStoreName] = useState("Reliance Smart, Sector 62");
  const [coords, setCoords] = useState({ lat: 28.6289, lng: 77.3653 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Get live GPS on load
  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      });
    }
  }, []);

  const handleAudit = async () => {
    setLoading(true);
    try {
      const scorecard = await MetroApi.submitScan(images, {
        store_name: storeName,
        latitude: coords.lat,
        longitude: coords.lng,
      });
      setResult(scorecard);
    } catch (err) {
      alert("Inspection failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <input type="file" multiple onChange={(e) => setImages(Array.from(e.target.files))} />
      <button onClick={handleAudit} disabled={loading} className="bg-blue-900 text-white px-4 py-2 rounded">
        {loading ? "Analyzing 10 Rules..." : "Run Statutory Audit"}
      </button>

      {result && (
        <div className="mt-6 border p-4 rounded bg-gray-50">
          <h2 className="text-xl font-bold">Verdict: {result.overall_status} ({result.compliance_score}%)</h2>
          <div className="mt-4">
            <a href={`http://localhost:8000/api/v1/scan/${result.scan_id}/certificate.pdf`} target="_blank" rel="noreferrer" className="bg-black text-white px-3 py-1 rounded text-sm">
              Download PDF Certificate
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 6. Complete API Reference Matrix

All endpoints run on `http://localhost:8000`:

| Method | Endpoint | Description | Query / Body Params | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/scan/analyze` | Multi-image package compliance audit | `images` (1-6 files), `store_name`, `latitude`, `longitude` | Full 10-rule scorecard JSON with `pdf_url` |
| `GET` | `/api/v1/scan/{scan_id}/certificate.pdf` | Direct stream of official court-admissible PDF | `store_name`, `latitude`, `longitude`, `officer_name`, `badge_id` | Binary `application/pdf` (instant render) |
| `GET` | `/api/v1/scan/{scan_id}` | Retrieve complete inspection audit dossier | None | Full declarations checklist JSON |
| `POST` | `/api/v1/scan/{scan_id}/email` | Dispatches official legal notice to email | `recipient_email`, `recipient_name`, `store_name` | Delivery status confirmation |
| `GET` | `/api/v1/dashboard/stats` | National inspection KPIs & violation counts | None | Total scans, today scans, violation % |
| `GET` | `/api/v1/dashboard/heatmap` | GIS coordinates of all audited packages | None | Array of `{latitude, longitude, status}` |
| `GET` | `/api/v1/dashboard/recent-scans` | Searchable & filterable inspection registry | `limit`, `q` (search term), `status` filter | List of inspection records |
| `GET` | `/api/v1/auth/me` | Validates JWT & retrieves logged-in inspector | `Bearer <token>` | User profile, badge ID, role |
| `GET` | `/health` | Server heartbeat & configuration status | None | Status `online`, Supabase, Cloudinary status |

---

## 7. How to Run the System

```bash
# 1. Activate your Python environment
cd backend

# 2. Run the full production FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Open in Web Browser:
# Web Portal: http://localhost:8000
# Interactive API Docs: http://localhost:8000/docs
```
