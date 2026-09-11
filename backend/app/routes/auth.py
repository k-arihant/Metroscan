# ============================================================
# METROSCAN AUTHENTICATION ROUTES
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional
from app.services.auth_service import AuthService
from app.dependencies import get_current_user_optional, get_current_user_required

router = APIRouter()


class SignUpRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email address")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = "consumer"  # "consumer" | "inspector" | "admin"
    badge_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email address")
    password: str = Field(..., min_length=1)


@router.post("/signup")
def sign_up(req: SignUpRequest):
    """Register a new citizen consumer or official inspector."""
    result = AuthService.sign_up(
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role or "consumer",
        badge_id=req.badge_id,
        department=req.department,
        designation=req.designation,
    )
    return result


@router.post("/login")
def login(req: LoginRequest):
    """Authenticate user and retrieve session token and role."""
    result = AuthService.sign_in(req.email, req.password)
    return result


class DemoLoginRequest(BaseModel):
    role: Optional[str] = "consumer"


@router.post("/demo-login")
def demo_login(req: DemoLoginRequest):
    """Isolated development demo login clearly distinguished from production auth."""
    return AuthService.demo_login(req.role or "consumer")


@router.get("/me")
def get_current_user(user: Optional[dict] = Depends(get_current_user_optional)):
    """Check currently active session via Bearer token."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session. Provide valid Bearer token.",
        )
    return {
        "status": "authenticated",
        "authenticated": True,
        "user_id": user.get("id"),
        "role": user.get("role", "consumer"),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "badge_id": user.get("badge_id"),
        "department": user.get("department"),
    }

