from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

class ValidationExpression(BaseModel):
    """
    Structured expression driving data-driven validation in the deterministic engine.
    """
    regex: Optional[str] = None
    forbidden_units_regex: Optional[str] = None
    allowed_units: Optional[List[str]] = None
    weight_threshold_g: Optional[float] = None
    min_pixel_height: Optional[int] = None
    confidence_threshold: Optional[float] = 0.70
    custom_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class RegulatoryDocumentDTO(BaseModel):
    id: str
    document_name: str
    document_type: str
    notification_number: Optional[str] = None
    publication_date: str
    effective_date: str
    source_url: Optional[str] = None
    source_reference: str
    content_hash: Optional[str] = None
    version: str
    status: str
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None


class RegulatoryDocumentCreate(BaseModel):
    document_name: str
    document_type: str = "AMENDMENT"
    notification_number: Optional[str] = None
    publication_date: str
    effective_date: str
    source_url: Optional[str] = None
    source_reference: str
    content_hash: Optional[str] = None
    version: str
    status: str = "PENDING_REVIEW"


class RegulatoryRuleDTO(BaseModel):
    id: str
    rule_id: str
    rule_version: str
    title: str
    section: str
    sub_rule: Optional[str] = None
    requirement: str
    applicable_categories: List[str]
    field_to_validate: str
    validation_type: str
    validation_expression: Optional[Dict[str, Any]] = None
    severity: str
    effective_from: str
    effective_until: Optional[str] = None
    source_document_id: Optional[str] = None
    source_url: Optional[str] = None
    source_page: Optional[str] = None
    source_excerpt: Optional[str] = None
    status: str
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None


class RegulatoryRuleCreate(BaseModel):
    rule_id: str
    rule_version: str
    title: str
    section: str
    sub_rule: Optional[str] = None
    requirement: str
    applicable_categories: List[str] = ["all", "packaged_commodity"]
    field_to_validate: str
    validation_type: str
    validation_expression: Optional[Dict[str, Any]] = None
    severity: str = "CRITICAL"
    effective_from: str
    effective_until: Optional[str] = None
    source_document_id: Optional[str] = None
    source_url: Optional[str] = None
    source_page: Optional[str] = None
    source_excerpt: Optional[str] = None
    status: str = "PENDING_REVIEW"


class RuleAmendmentDTO(BaseModel):
    id: str
    document_id: str
    rule_id: str
    change_type: str
    previous_value: Optional[str] = None
    new_value: str
    effective_from: str
    effective_until: Optional[str] = None
    explanation: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None


class RuleStatusTransitionRequest(BaseModel):
    action: str = Field(..., description="APPROVE, ACTIVATE, SUPERSEDE, REJECT")
    effective_until: Optional[str] = None
    reviewer_notes: Optional[str] = None


class RegulatoryCatalogSummaryResponse(BaseModel):
    total_rules: int
    active_rules: int
    pending_rules: int
    superseded_rules: int
    documents_count: int
    amendments_count: int
    available_versions: List[str]
    latest_version: str
