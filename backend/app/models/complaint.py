from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True, nullable=False)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    product_name = Column(String(255), nullable=True)
    manufacturer_name = Column(String(255), nullable=True)
    commodity_category = Column(String(100), default="packaged_commodity", nullable=False)

    status = Column(String(50), default="PENDING_NOTICE", nullable=False)  # PENDING_NOTICE, NOTICE_ISSUED, HEARING_SCHEDULED, CLOSED
    statutory_provisions = Column(Text, nullable=True)  # e.g. Rule 6(1)(e), Rule 18(1)
    violations_json = Column(JSON, nullable=True)  # Detailed list of non-compliant checks
    evidence_summary_json = Column(JSON, nullable=True)  # Attached bounding boxes and image crops
    enforcement_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", backref="complaint_record", foreign_keys=[inspection_id])
    product = relationship("Product", backref="complaints", foreign_keys=[product_id])
    inspector = relationship("User", backref="submitted_complaints", foreign_keys=[inspector_id])
