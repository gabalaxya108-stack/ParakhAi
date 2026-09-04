from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    provider = Column(String(100), nullable=False)
    raw_text = Column(Text, nullable=True)
    total_blocks = Column(Integer, default=0, nullable=False)
    processing_time_ms = Column(Float, default=0.0, nullable=False)
    blocks_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("Inspection", back_populates="ocr_results")
    image = relationship("Image", back_populates="ocr_results")
