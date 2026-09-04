from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    status = Column(String(50), default="UPLOADED", nullable=False)
    overall_status = Column(String(50), default="NOT_EVALUATED", nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    model_provider_version = Column(String(100), default="mock-vision-v1", nullable=False)
    rule_version = Column(String(50), default="2026.1", nullable=False)
    review_status = Column(String(50), default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    inspector = relationship("User", back_populates="inspections")
    product = relationship("Product", back_populates="inspections")
    images = relationship("Image", back_populates="inspection", cascade="all, delete-orphan")
    ocr_results = relationship("OCRResult", back_populates="inspection", cascade="all, delete-orphan")
    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="inspection", cascade="all, delete-orphan")
    reviews = relationship("InspectionReview", back_populates="inspection", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="inspection", cascade="all, delete-orphan")
