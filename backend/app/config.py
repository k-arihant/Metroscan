import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in backend directory, current working directory, and parent directory
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_workspace_dir = _backend_dir.parent

for _p in [_backend_dir / ".env", _workspace_dir / ".env", Path(".env")]:
    if _p.exists():
        load_dotenv(_p, override=False)


class Settings:
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Mock mode toggle
    USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

    # Email / SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "yashnikam1310@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "yashnikam1310@gmail.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "MetroScan Legal Metrology Enforcement Portal")

    # Security & Limits
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "15"))


settings = Settings()
