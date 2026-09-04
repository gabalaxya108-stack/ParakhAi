from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    check_id = Column(Integer, ForeignKey("compliance_checks.id"), nullable=True)
    rule_id = Column(String(100), nullable=False, index=True)
    field = Column(String(100), nullable=False)
    violation_type = Column(String(50), nullable=False)  # MISSING_DECLARATION, NON_STANDARD_UNIT, FORMAT_DEFECT
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="violations")
    check = relationship("ComplianceCheck", back_populates="violations")
