from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DashboardMetricsResponse(BaseModel):
    total_inspections: int = Field(..., description="Total inspection records stored")
    compliant_count: int = Field(..., description="Packages evaluated fully compliant")
    potential_violations_count: int = Field(..., description="Packages flagged with potential statutory violations")
    manual_review_count: int = Field(..., description="Packages requiring human inspector verification")
    pending_evaluation_count: int = Field(..., description="Packages uploaded but not yet evaluated")
    average_risk_score: float = Field(..., description="Mean calculated risk score across evaluated packages")
    recent_inspections: List[Dict[str, Any]] = Field(..., description="Recent inspection activity feed")
