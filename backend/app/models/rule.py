from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(100), index=True, nullable=False)  # e.g. "LM-MRP-001"
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirement = Column(Text, nullable=False)
    applicable_product_categories = Column(JSON, nullable=False)  # list of strings
    field_to_validate = Column(String(100), nullable=False)
    validation_type = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    source_reference = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    rule_version_rel = relationship("RuleVersion", back_populates="rules")
