from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class InspectionReview(Base):
    __tablename__ = "inspection_reviews"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, ACTION_REQUIRED
    notes = Column(Text, nullable=True)
    decision_timestamp = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
