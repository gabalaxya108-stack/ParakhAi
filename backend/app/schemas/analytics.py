from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class RepeatedIssue(BaseModel):
    field: str = Field(..., description="Field name where statutory issue recurred (e.g. 'mrp', 'net_quantity')")
    label: str = Field(..., description="Human-readable label (e.g. 'MRP Declaration')")
    count: int = Field(..., description="Number of times this issue was flagged for this manufacturer")
    rule_id: Optional[str] = Field(None, description="Primary rule ID associated with this issue")
    violation_type: Optional[str] = Field(None, description="Violation type (e.g. 'MISSING_DECLARATION')")

class ManufacturerAnalyticsItem(BaseModel):
    manufacturer_name: str = Field(..., description="Legal name of commodity manufacturer or packer")
    total_inspections: int = Field(..., description="Total commodity inspections recorded")
    compliant_inspections: int = Field(..., description="Total compliant package screenings")
    potential_violations: int = Field(..., description="Total packages flagged with potential violations")
    manual_reviews: int = Field(..., description="Total packages flagged for manual inspector review")
    violation_categories: Dict[str, int] = Field(default_factory=dict, description="Counts broken down by statutory category")
    repeated_issues: List[RepeatedIssue] = Field(default_factory=list, description="Repeated potential issues detected across historical audits")
    compliance_rate: float = Field(..., description="Percentage of compliant inspections (0.0 to 100.0)")
    average_risk: float = Field(..., description="Average non-compliance risk score (0 to 100)")
    status_label: str = Field(..., description="Statutorily neutral status indicator (e.g. 'Repeated potential issues detected.')")
    latest_inspection_date: Optional[str] = Field(None, description="ISO timestamp of most recent inspection")

class ManufacturerAnalyticsResponse(BaseModel):
    total_manufacturers: int = Field(..., description="Count of distinct manufacturers analyzed")
    total_inspections: int = Field(..., description="Total inspections aggregated in query scope")
    total_potential_violations: int = Field(..., description="Cumulative potential violations across all manufacturers")
    total_repeated_issues: int = Field(..., description="Total count of recurring potential declaration issues")
    manufacturers: List[ManufacturerAnalyticsItem] = Field(..., description="Aggregated analytics per manufacturer")
