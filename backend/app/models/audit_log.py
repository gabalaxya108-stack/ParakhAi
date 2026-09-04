from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # IMAGE_UPLOADED, OCR_PROCESSED, EXTRACTION_COMPLETED, COMPLIANCE_EVALUATED, REVIEW_SUBMITTED
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True)
    change_details_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
