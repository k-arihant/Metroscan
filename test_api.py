"""
Quick API Test — Run this to test MetroScan end-to-end
"""
import requests
import json

BASE = "http://localhost:8000"

print("=" * 60)
print("  METROSCAN LIVE API TEST")
print("=" * 60)

# 1. Health check
print("\n--- 1. Health Check ---")
r = requests.get(f"{BASE}/health")
print(json.dumps(r.json(), indent=2))

# 2. Scan analyze (mock mode)
print("\n--- 2. Scan Analyze (upload image) ---")
jpeg = bytes([0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,
              0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,
              0x00,0x01,0x00,0x00,0xFF,0xD9])
files = [("images", ("test_product.jpg", jpeg, "image/jpeg"))]
form = {
    "store_name": "Kirana Store Mumbai",
    "latitude": "19.076",
    "longitude": "72.877",
    "category": "food",
}
r = requests.post(f"{BASE}/api/v1/scan/analyze", files=files, data=form)
result = r.json()

print(f"  Product : {result['product_name']}")
print(f"  Brand   : {result['brand_name']}")
print(f"  Status  : {result['overall_status']}")
print(f"  Score   : {result['compliance_score']}")
print(f"  Scan ID : {result['scan_id']}")
print()

for d in result["declarations"]:
    val = d["extracted_value"] if d["extracted_value"] else "(missing)"
    icon = {"PASS": "PASS", "FAIL": "FAIL", "WARNING": "WARN"}.get(d["status"], d["status"])
    print(f"  [{icon:4s}] {d['rule_name']:42s} | {val}")
    if d.get("violation_reason"):
        print(f"         >> {d['violation_reason']}")

scan_id = result["scan_id"]

# 3. Get scan details
print("\n--- 3. Get Scan Details ---")
r = requests.get(f"{BASE}/api/v1/scan/{scan_id}")
print(f"  Status: {r.status_code}, declarations: {len(r.json()['declarations'])}")

# 4. Generate PDF certificate
print("\n--- 4. PDF Certificate ---")
r = requests.get(f"{BASE}/api/v1/scan/{scan_id}/certificate.pdf",
                 params={"store_name": "Kirana Store", "latitude": 19.076, "longitude": 72.877})
print(f"  PDF size: {len(r.content)} bytes")
print(f"  SHA-256: {r.headers.get('x-sha256-hash', 'N/A')}")

# 5. Dashboard stats
print("\n--- 5. Dashboard Stats ---")
r = requests.get(f"{BASE}/api/v1/dashboard/stats")
s = r.json()
print(f"  Total Scans: {s['total_scans']}")
print(f"  Today: {s['today_scans']}")
print(f"  Violations: {s['violations_detected']}")
print(f"  Compliance Rate: {s['compliance_rate']}%")

# 6. Heatmap
print("\n--- 6. Heatmap ---")
r = requests.get(f"{BASE}/api/v1/dashboard/heatmap")
pins = r.json()
print(f"  {len(pins)} geo-pins returned")
for p in pins[:3]:
    print(f"    ({p['latitude']}, {p['longitude']}) - {p['overall_status']} - {p.get('store_name','')}")

# 7. Recent scans
print("\n--- 7. Recent Scans ---")
r = requests.get(f"{BASE}/api/v1/dashboard/recent-scans")
scans = r.json()
print(f"  {len(scans)} recent scans")
for s in scans[:3]:
    print(f"    {s['product_name']:30s} | {s['overall_status']:15s} | Score: {s['compliance_score']}")

print("\n" + "=" * 60)
print("  ALL TESTS COMPLETE")
print("=" * 60)
