# ============================================================
# METROSCAN AUTHENTICATION SERVICE
# Dual-Role Authentication: Official Inspector vs Citizen Consumer
# Backed by Supabase Auth & PostgreSQL Profiles
# ============================================================

from fastapi import HTTPException, status
from typing import Optional, Dict
from app.services.db_service import DBService, get_supabase


class AuthService:
    """
    Manages user authentication, profile creation,
    and role-based permissions (Consumer vs Inspector vs Admin).
    """

    @staticmethod
    def sign_up(
        email: str,
        password: str,
        full_name: str,
        role: str = "consumer",
        badge_id: Optional[str] = None,
        department: Optional[str] = None,
        designation: Optional[str] = None,
    ) -> Dict:
        """
        Registers a new user in Supabase Auth and inserts their profile.
        """
        sb = get_supabase()
        try:
            # 1. Create auth user in Supabase with admin API or standard sign_up
            try:
                auth_res = sb.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name, "role": role},
                })
                user = auth_res.user
            except Exception:
                auth_res = sb.auth.sign_up({"email": email, "password": password})
                user = auth_res.user

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to register user in Supabase Auth.",
                )

            # 2. Insert into profiles table
            profile_data = {
                "id": user.id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "badge_id": badge_id if role in ("inspector", "admin") else None,
                "department": department if role in ("inspector", "admin") else None,
                "designation": designation if role in ("inspector", "admin") else None,
            }
            sb.table("profiles").upsert(profile_data).execute()

            # 3. Sign in to get active session
            token = None
            try:
                login_res = sb.auth.sign_in_with_password({"email": email, "password": password})
                if login_res.session:
                    token = login_res.session.access_token
            except Exception:
                token = getattr(auth_res.session, "access_token", None) if hasattr(auth_res, "session") and auth_res.session else None

            return {
                "status": "success",
                "user_id": user.id,
                "email": email,
                "role": role,
                "full_name": full_name,
                "badge_id": badge_id,
                "department": department,
                "access_token": token,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}",
            )

    @staticmethod
    def sign_in(email: str, password: str) -> Dict:
        """
        Authenticates an existing user and fetches their profile & role.
        Enforces strict authentication against Supabase Auth.
        """
        sb = get_supabase()
        try:
            auth_res = sb.auth.sign_in_with_password({"email": email.strip(), "password": password})
            user = auth_res.user
            if not user or not auth_res.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            # Fetch authoritative profile from PostgreSQL
            profile = DBService.get_profile(user.id)
            role = profile.get("role", "consumer") if profile else "consumer"
            badge_id = profile.get("badge_id") if profile else None
            department = profile.get("department") if profile else None
            full_name = profile.get("full_name") if profile else (user.user_metadata.get("full_name") or email.split('@')[0])

            return {
                "status": "success",
                "user_id": user.id,
                "email": user.email,
                "role": role,
                "full_name": full_name,
                "badge_id": badge_id,
                "department": department,
                "access_token": auth_res.session.access_token,
            }
        except HTTPException:
            raise
        except Exception as e:
            err_msg = str(e)
            if "invalid" in err_msg.lower() or "credentials" in err_msg.lower() or "grant" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {err_msg}",
            )

    @staticmethod
    def demo_login(role: str) -> Dict:
        """
        Isolated development demo login clearly distinguished from production auth.
        """
        if role in ("inspector", "admin"):
            return {
                "status": "demo_success",
                "user_id": "c260dd91-896c-4177-9181-0af176c9c811",
                "email": "inspector@legalmetrology.gov.in",
                "role": "inspector",
                "full_name": "Inspector Rajesh Kumar Sharma",
                "badge_id": "LM-DEL-8492",
                "department": "Delhi State Legal Metrology Enforcement Division",
                "access_token": "demo-jwt-inspector-active",
            }
        return {
            "status": "demo_success",
            "user_id": "64513de0-54dd-4e61-910b-dae8b19bf721",
            "email": "citizen@example.in",
            "role": "consumer",
            "full_name": "Priya Mehta",
            "badge_id": None,
            "department": None,
            "access_token": "demo-jwt-consumer-active",
        }
