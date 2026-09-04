import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class RegulatoryDocument(Base):
    """
    Official government regulatory documents published by the
    Department of Consumer Affairs / Ministry of Consumer Affairs, Food & Public Distribution.
    """
    __tablename__ = "regulatory_documents"

    id = Column(String(64), primary_key=True, default=lambda: f"doc_{uuid.uuid4().hex[:12]}")
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # ACT, RULES, AMENDMENT, ADVISORY, CORRIGENDUM
    notification_number = Column(String(100), nullable=True)  # e.g., "G.S.R. 202(E)", "G.S.R. 226(E)"
    publication_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    effective_date = Column(String(20), nullable=False)    # YYYY-MM-DD
    source_url = Column(String(512), nullable=True)
    source_reference = Column(String(255), nullable=False)  # e.g., "Gazette of India, Extraordinary, Part II"
    content_hash = Column(String(64), nullable=True)        # SHA-256 hash of official document
    version = Column(String(50), nullable=False)            # e.g., "2011", "2017", "2021", "2022", "2026.1"
    status = Column(String(50), default="ACTIVE", nullable=False)  # PENDING_REVIEW, APPROVED, ACTIVE, SUPERSEDED, REJECTED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    rules = relationship("RegulatoryRule", back_populates="source_document", cascade="all, delete-orphan")
    amendments = relationship("RuleAmendment", back_populates="document", cascade="all, delete-orphan")


class RegulatoryRule(Base):
    """
    Data-driven statutory rule definitions derived from official regulatory documents.
    """
    __tablename__ = "regulatory_rules"

    id = Column(String(64), primary_key=True, default=lambda: f"rule_{uuid.uuid4().hex[:12]}")
    rule_id = Column(String(100), index=True, nullable=False)  # e.g. "PCR-R6-001", "LM-MRP-001"
    rule_version = Column(String(50), index=True, nullable=False)  # e.g. "2011", "2017", "2021", "2022", "2026.1"
    title = Column(String(255), nullable=False)
    section = Column(String(100), nullable=False)  # e.g. "Rule 6", "Section 36"
    sub_rule = Column(String(100), nullable=True)  # e.g. "6(1)(e)", "6(11)"
    requirement = Column(Text, nullable=False)
    applicable_categories = Column(JSON, nullable=False)  # ["all"], ["packaged_commodity"], etc.
    field_to_validate = Column(String(100), index=True, nullable=False)  # "mrp", "net_quantity", etc.
    validation_type = Column(String(50), nullable=False)  # REQUIRED, CONDITIONAL, FORMAT_CHECK, VALUE_CHECK, READABILITY_CHECK, MANUAL_REVIEW, UNIT_SPECIFICATION, ECOM_LISTING_MATCH
    validation_expression = Column(JSON, nullable=True)  # Structured configuration/expression driving evaluation
    severity = Column(String(50), default="CRITICAL", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    effective_from = Column(String(20), nullable=False)  # YYYY-MM-DD
    effective_until = Column(String(20), nullable=True)  # YYYY-MM-DD or None if currently active
    source_document_id = Column(String(64), ForeignKey("regulatory_documents.id"), nullable=True)
    source_url = Column(String(512), nullable=True)
    source_page = Column(String(50), nullable=True)
    source_excerpt = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # PENDING_REVIEW, APPROVED, ACTIVE, SUPERSEDED, REJECTED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    source_document = relationship("RegulatoryDocument", back_populates="rules")


class RuleAmendment(Base):
    """
    Historical amendment records tracking legislative changes across rule versions.
    """
    __tablename__ = "rule_amendments"

    id = Column(String(64), primary_key=True, default=lambda: f"amend_{uuid.uuid4().hex[:12]}")
    document_id = Column(String(64), ForeignKey("regulatory_documents.id"), nullable=False)
    rule_id = Column(String(100), index=True, nullable=False)
    change_type = Column(String(50), nullable=False)  # INSERTION, SUBSTITUTION, DELETION, CLARIFICATION
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    effective_from = Column(String(20), nullable=False)
    effective_until = Column(String(20), nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("RegulatoryDocument", back_populates="amendments")
