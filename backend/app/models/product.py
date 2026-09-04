from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    brand = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False, default="packaged_commodity")
    manufacturer = Column(Text, nullable=True)
    packer = Column(Text, nullable=True)
    importer = Column(Text, nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    inspections = relationship("Inspection", back_populates="product")
