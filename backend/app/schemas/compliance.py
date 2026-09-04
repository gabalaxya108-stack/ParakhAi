from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class SubCheckItemDTO(BaseModel):
    rule_id: str
    rule_title: str
    section: Optional[str] = 'Rule 6'
    status: str  # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_APPLICABLE
    reason: str
    confidence: float
    extracted_value: Optional[str] = None
    severity: str = "MEDIUM"

class CanonicalRequirementDTO(BaseModel):
    canonical_id: str  # e.g. REQ-MRP, REQ-NET-QTY
    title: str        # e.g. "Maximum Retail Price (MRP)"
    statutory_rule: str # e.g. "Rule 6(1)(e) & 6(11)"
    field: str        # e.g. "mrp"
    status: str       # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, NOT_APPLICABLE
    extracted_value: Optional[str] = None
    confidence: float
    overall_reason: str
    sub_checks: List[SubCheckItemDTO] = Field(default_factory=list)
    human_review: Optional[Dict[str, Any]] = None

class RuleCheckResult(BaseModel):
    """
    Evaluation result for a single statutory rule check with full official traceability.
    """
    rule_id: str = Field(..., description="Statutory rule identifier (e.g. PCR-R6-001)")
    rule_version: Optional[str] = Field(None, description="Statutory rule version tag (e.g. 2026.1)")
    requirement: str = Field(..., description="Legal requirement description")
    field: str = Field(..., description="Target declaration field (e.g. mrp, net_quantity)")
    extracted_value: Optional[str] = Field(None, description="Value extracted from package label or null")
    detection_status: str = Field(
        ...,
        description="FOUND | NOT_FOUND | UNCLEAR | NOT_APPLICABLE"
    )
    status: str = Field(
        ...,
        description="COMPLIANT | NON_COMPLIANT | NEEDS_REVIEW | NOT_APPLICABLE | POTENTIAL_VIOLATION | MANUAL_REVIEW"
    )
    reason: str = Field(..., description="Explainable deterministic reasoning for the check outcome")
    severity: str = Field(..., description="Violation severity level (CRITICAL, HIGH, MEDIUM, LOW)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the perception source")
    section: Optional[str] = Field(None, description="Statutory section (e.g. Rule 6)")
    sub_rule: Optional[str] = Field(None, description="Sub-rule specification (e.g. 6(1)(e))")
    effective_date: Optional[str] = Field(None, description="Date when this statutory requirement took effect")
    source_document: Optional[str] = Field(None, description="Official government source publication")
    source_url: Optional[str] = Field(None, description="Link to official government gazette or notification")
    source_page: Optional[str] = Field(None, description="Official document page or excerpt citation")
    evidence_reference: Optional[Dict[str, Any]] = Field(
        None,
        description="Spatial coordinates, source block, or page grounding"
    )

    model_config = ConfigDict(from_attributes=True)

class ComplianceEvaluationResult(BaseModel):
    """
    Complete deterministic compliance evaluation output.
    """
    inspection_id: str = Field(..., description="Contextual inspection identifier")
    overall_status: str = Field(
        ...,
        description="COMPLIANT | NON_COMPLIANT | NEEDS_REVIEW | POTENTIAL_VIOLATION | MANUAL_REVIEW"
    )
    risk_score: int = Field(..., ge=0, le=100, description="Calculated non-compliance risk score (0-100)")
    screening_priority_score: int = Field(default=0, ge=0, le=100, description="Advisory screening priority score (0-100) — not a legal penalty")
    confirmed_violations_count: int = Field(default=0, description="Number of confirmed statutory violations")
    items_needing_review_count: int = Field(default=0, description="Number of declarations requiring human review")
    evidence_coverage_percent: float = Field(default=100.0, description="Percentage of required declarations with clear visual evidence")
    canonical_requirements: List[CanonicalRequirementDTO] = Field(
        default_factory=list,
        description="Unified canonical requirements grouping granular sub-checks"
    )
    violations: List[RuleCheckResult] = Field(
        default_factory=list,
        description="List of checks that failed compliance"
    )
    checks: List[RuleCheckResult] = Field(
        default_factory=list,
        description="Complete list of all rule evaluations performed"
    )
    human_reviews: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Inspector manual review overrides and audit metadata"
    )
    product_category: str = Field(..., description="Applicable product category used for screening")
    rule_version: str = Field(..., description="Version of the codified rule engine catalog used")
    rules_evaluated: Optional[List[str]] = Field(default_factory=list, description="List of rule IDs evaluated")
    timestamp: str = Field(..., description="UTC ISO-8601 evaluation timestamp")

    model_config = ConfigDict(from_attributes=True)
