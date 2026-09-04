from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class RuleModel(BaseModel):
    rule_id: str = Field(..., description="Unique legal rule identifier (e.g. LM-MRP-001)")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Summary of the rule objective")
    requirement: str = Field(..., description="Precise statutory requirement for compliance")
    applicable_product_categories: List[str] = Field(
        default_factory=lambda: ["all"],
        description="Target categories (e.g. ['all'], ['food'], ['beverages'])"
    )
    field_to_validate: str = Field(..., description="Target declaration field (e.g. mrp, net_quantity)")
    validation_type: str = Field(..., description="Type of check: REQUIRED, FORMAT, UNIT_SPECIFICATION, etc.")
    severity: str = Field(..., description="Violation severity level: CRITICAL, HIGH, MEDIUM, LOW")
    effective_from: str = Field(..., description="Effective start date (YYYY-MM-DD)")
    effective_until: Optional[str] = Field(None, description="Sunset or superseded date (YYYY-MM-DD), or null")
    rule_version: str = Field(..., description="Version of the codified rule engine catalog (e.g. 2026.1)")
    source_reference: str = Field(..., description="Official citation under Legal Metrology Act / Rules")
    enabled: bool = Field(True, description="Whether this rule is currently evaluated")

    model_config = ConfigDict(from_attributes=True)

class RuleListResponse(BaseModel):
    rules: List[RuleModel] = Field(..., description="List of matching rule definitions")
    total: int = Field(..., description="Total count of returned rules")
    selected_version: str = Field(..., description="Active or queried rule catalog version")
    available_versions: List[str] = Field(..., description="All discoverable rule catalog versions")

    model_config = ConfigDict(from_attributes=True)
