from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from backend.app.core.security import require_role, require_any_role, AuthUser, get_current_user
from backend.app.db.session import SessionLocal
from backend.app.models import User, AuditLog, Rule
from backend.app.core.logging import get_logger

logger = get_logger("api.admin")
router = APIRouter()

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field("INSPECTOR", description="INSPECTOR | SUPERVISOR | ADMIN")

class UserRecordResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    created_at: str

class AuditLogItemResponse(BaseModel):
    id: int
    inspection_id: Optional[int]
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[str]
    change_details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    timestamp: str

@router.get(
    "/admin/roles/current",
    summary="Get current user identity and RBAC role",
    description="Returns current authenticated user identity and resolved Microsoft Entra ID role permissions."
)
async def get_current_user_role(current_user: AuthUser = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "entra_oid": current_user.entra_oid
    }

@router.get(
    "/admin/audit-logs",
    response_model=List[AuditLogItemResponse],
    summary="Retrieve immutable system audit logs",
    description="Supervisor and Admin role access only. Returns chronological regulatory ledger of all system actions."
)
async def list_audit_logs(
    limit: int = Query(50, le=200),
    current_user: AuthUser = Depends(require_any_role(["SUPERVISOR", "ADMIN"]))
):
    logger.info(f"Audit log accessed by {current_user.username} ({current_user.role})")
    with SessionLocal() as db:
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [
            AuditLogItemResponse(
                id=log.id,
                inspection_id=log.inspection_id,
                user_id=log.user_id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                change_details=log.change_details_json,
                ip_address=log.ip_address,
                timestamp=log.timestamp.isoformat()
            )
            for log in logs
        ]

@router.get(
    "/admin/users",
    response_model=List[UserRecordResponse],
    summary="List all registered platform users",
    description="Admin role access only. Lists all registered inspectors, supervisors, and administrators."
)
async def list_users(
    current_user: AuthUser = Depends(require_role("ADMIN"))
):
    logger.info(f"User management list requested by Admin '{current_user.username}'")
    with SessionLocal() as db:
        users = db.query(User).order_by(User.id).all()
        return [
            UserRecordResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                created_at=u.created_at.isoformat()
            )
            for u in users
        ]

@router.post(
    "/admin/users",
    response_model=UserRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new platform user with assigned role",
    description="Admin role access only. Creates an inspector, supervisor, or admin user."
)
async def create_user(
    payload: UserCreateRequest,
    current_user: AuthUser = Depends(require_role("ADMIN"))
):
    logger.info(f"User provisioning requested by Admin '{current_user.username}': new_user='{payload.username}', role='{payload.role}'")
    with SessionLocal() as db:
        existing = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username '{payload.username}' or email '{payload.email}' already exists."
            )

        new_user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role.upper()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserRecordResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            created_at=new_user.created_at.isoformat()
        )
