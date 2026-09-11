from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import scan, dashboard, auth

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="MetroScan Compliance API",
    description="Backend API for Automated Legal Metrology Compliance Verification System",
    version="1.0.0",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path, methods in schema.get("paths", {}).items():
        for method, details in methods.items():
            content = details.get("requestBody", {}).get("content", {})
            if "multipart/form-data" in content:
                m_schema = content["multipart/form-data"].get("schema", {})
                ref = m_schema.get("$ref", "")
                if ref:
                    name = ref.split("/")[-1]
                    comp = schema.get("components", {}).get("schemas", {}).get(name, {})
                    if "images" in comp.get("properties", {}):
                        comp["properties"]["images"] = {
                            "type": "array",
                            "items": {"type": "string", "format": "binary"},
                            "description": "1-6 package photographs",
                        }
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi

# ── CORS: Allow Flutter Web and Mobile to connect from anywhere ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins during hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register route modules ──
app.include_router(scan.router, prefix="/api/v1/scan", tags=["Scanning"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])


import os
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse

@app.get("/", include_in_schema=False)
def root(request: Request):
    """
    Root endpoint:
    Redirects browser requests to the authoritative React Web Portal (port 5173).
    API consumers receive system status and route metadata.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="http://localhost:5173", status_code=307)
    return {
        "system": "MetroScan Compliance Backend",
        "status": "online",
        "version": "1.0.0",
        "web_portal": "http://localhost:5173",
        "endpoints": {
            "scan": "/api/v1/scan/analyze",
            "dashboard_stats": "/api/v1/dashboard/stats",
            "heatmap": "/api/v1/dashboard/heatmap",
            "recent_scans": "/api/v1/dashboard/recent-scans",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    from app.config import settings
    return {
        "status": "online",
        "mock_mode": settings.USE_MOCK,
        "supabase_configured": bool(settings.SUPABASE_URL),
        "cloudinary_configured": bool(settings.CLOUDINARY_CLOUD_NAME),
    }
