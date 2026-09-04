import re
import os
from typing import List, Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("core.security")

class AuthUser(BaseModel):
    id: int = 1
    username: str = "inspector_lm"
    email: str = "inspector@legalmetrology.gov.in"
    full_name: str = "Inspector General of Legal Metrology"
    role: str = "INSPECTOR"  # INSPECTOR, SUPERVISOR, ADMIN
    entra_oid: Optional[str] = None

# Role hierarchy definitions
ROLE_PERMISSIONS = {
    "INSPECTOR": ["inspections:create", "inspections:read", "inspections:review"],
    "SUPERVISOR": ["inspections:create", "inspections:read", "inspections:review", "analytics:read", "audit:read"],
    "ADMIN": ["inspections:create", "inspections:read", "inspections:review", "analytics:read", "audit:read", "users:manage", "rules:manage"]
}

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes untrusted filenames to prevent directory traversal and injection attacks.
    """
    if not filename:
        return "unnamed_asset.jpg"

    # 1. Normalize separators and strip path components
    normalized = filename.replace("\\", "/")
    basename = normalized.split("/")[-1]

    # 2. Remove null bytes and control chars
    basename = re.sub(r'[\x00-\x1f\x7f]', '', basename)

    # 3. Replace dangerous characters (semicolons, spaces, ampersands, pipes, etc.)
    cleaned = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)

    # 4. Avoid hidden files or leading dots
    cleaned = cleaned.lstrip(".")

    return cleaned if cleaned else "unnamed_asset.jpg"

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> AuthUser:
    """
    Resolves the authenticated user.
    Designed for Microsoft Entra ID (Azure AD) OAuth2 Bearer tokens,
    with development prototype role-switching support via X-User-Role header.
    """
    # 1. Microsoft Entra ID Bearer Token Handling
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            # Prototype Entra ID mock claims parser / token verification
            if token == "admin-token":
                return AuthUser(username="admin_lm", role="ADMIN", full_name="Legal Metrology Admin", entra_oid="entra-admin-001")
            elif token == "supervisor-token":
                return AuthUser(username="supervisor_lm", role="SUPERVISOR", full_name="Supervisory Officer", entra_oid="entra-sup-002")
        except Exception as e:
            logger.warning(f"Entra ID token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Microsoft Entra ID credentials."
            )

    # 2. Development Role-Header Support (Hackathon prototype convenience)
    selected_role = (x_user_role or "INSPECTOR").upper().strip()
    if selected_role not in ["INSPECTOR", "SUPERVISOR", "ADMIN"]:
        selected_role = "INSPECTOR"

    if selected_role == "ADMIN":
        return AuthUser(
            id=3,
            username="admin_gov",
            email="admin@legalmetrology.gov.in",
            full_name="Platform Administrator",
            role="ADMIN"
        )
    elif selected_role == "SUPERVISOR":
        return AuthUser(
            id=2,
            username="supervisor_patil",
            email="supervisor@legalmetrology.gov.in",
            full_name="Senior Enforcement Supervisor",
            role="SUPERVISOR"
        )
    else:
        return AuthUser(
            id=1,
            username="inspector_lm",
            email="inspector@legalmetrology.gov.in",
            full_name="Inspector General of Legal Metrology",
            role="INSPECTOR"
        )

def require_role(required_role: str):
    """
    FastAPI dependency factory enforcing a specific role.
    """
    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        role_hierarchy = {"INSPECTOR": 1, "SUPERVISOR": 2, "ADMIN": 3}
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role.upper(), 99)

        if user_level < required_level:
            logger.warning(f"Access forbidden: User '{current_user.username}' with role '{current_user.role}' tried to access {required_role} resource.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires '{required_role}' authorization level."
            )
        return current_user
    return role_checker

def require_any_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory allowing any of the listed roles.
    """
    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        allowed_normalized = [r.upper() for r in allowed_roles]
        if current_user.role not in allowed_normalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{current_user.role}' not in allowed roles {allowed_roles}."
            )
        return current_user
    return role_checker
