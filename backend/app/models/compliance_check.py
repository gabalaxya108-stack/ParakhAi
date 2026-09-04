from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String(100), nullable=False, index=True)
    field = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=True)
    detection_status = Column(String(50), nullable=False)  # FOUND, NOT_FOUND, UNCLEAR, NOT_APPLICABLE
    status = Column(String(50), nullable=False)  # COMPLIANT, POTENTIAL_VIOLATION, MANUAL_REVIEW, NOT_APPLICABLE
    reason = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    evidence_reference_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="compliance_checks")
    violations = relationship("Violation", back_populates="check")
    evidence = relationship("Evidence", back_populates="check")
