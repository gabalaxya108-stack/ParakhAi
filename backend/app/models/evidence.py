from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(100), unique=True, index=True, nullable=False)  # e.g. "ev_..."
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    check_id = Column(Integer, ForeignKey("compliance_checks.id"), nullable=True)
    rule_id = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # ABSENCE, INCORRECT_DECLARATION, UNCERTAIN, DETECTED_DECLARATION
    image_id = Column(String(255), nullable=False)
    bounding_box_json = Column(JSON, nullable=True)
    detected_text = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_available = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="evidence_items")
    check = relationship("ComplianceCheck", back_populates="evidence")
