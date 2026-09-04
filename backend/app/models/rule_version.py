from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(50), unique=True, index=True, nullable=False)  # e.g. "2026.1"
    description = Column(Text, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    rules = relationship("Rule", back_populates="rule_version_rel")
