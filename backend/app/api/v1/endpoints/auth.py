import hashlib
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field
from backend.app.db.session import SessionLocal
from backend.app.models import User

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Demo username (e.g. inspector.demo, officer.demo, admin.demo)")
    password: str = Field(..., description="Password")

class UserDTO(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserDTO

def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    if not hashed_password:
        return plain_password == "Parakh@123"
    computed = hashlib.sha256(f"parakh_salt_{plain_password}".encode("utf-8")).hexdigest()
    return computed == hashed_password or plain_password == "Parakh@123"

@router.post("/login", response_model=LoginResponse, summary="Authenticate User for Demo Roles")
def login(credentials: LoginRequest = Body(...)):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == credentials.username.strip()).first()
        if not user:
            # Check fallback demo credentials
            if credentials.username.strip() in ["inspector.demo", "officer.demo", "admin.demo", "inspector_lm"] and credentials.password == "Parakh@123":
                role_map = {
                    "inspector.demo": ("Rajesh Sharma (Inspector ID: INS-DL-4029)", "INSPECTOR"),
                    "officer.demo": ("Dr. Meenakshi Sundaram (Deputy Controller)", "OFFICER"),
                    "admin.demo": ("National Informatics Centre Administrator", "ADMIN"),
                    "inspector_lm": ("Inspector General of Legal Metrology", "INSPECTOR")
                }
                name, role = role_map.get(credentials.username.strip(), ("Demo Inspector", "INSPECTOR"))
                user = User(
                    username=credentials.username.strip(),
                    email=f"{credentials.username.strip()}@consumer.gov.in",
                    full_name=name,
                    role=role,
                    password_hash=hashlib.sha256(f"parakh_salt_{credentials.password}".encode("utf-8")).hexdigest()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password. Use demo accounts (e.g. inspector.demo / Parakh@123)."
                )

        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Use demo password Parakh@123."
            )

        token = f"parakh_demo_token_{user.username}_{user.role}"
        return LoginResponse(
            access_token=token,
            user=UserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role
            )
        )

@router.get("/me", response_model=UserDTO, summary="Get Current User Session")
def get_current_user_profile(username: Optional[str] = "inspector.demo"):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = db.query(User).first()
        if not user:
            return UserDTO(
                id=1,
                username="inspector.demo",
                email="inspector.demo@consumer.gov.in",
                full_name="Rajesh Sharma (Inspector ID: INS-DL-4029)",
                role="INSPECTOR"
            )
        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role
        )
