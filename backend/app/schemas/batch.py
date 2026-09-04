from typing import List, Optional
from pydantic import BaseModel, Field

class BatchInspectionItemResult(BaseModel):
    inspection_id: Optional[str] = Field(None, description="Generated inspection identifier, or null if failed")
    filename: str = Field(..., description="Original filename of uploaded package photograph")
    product_name: str = Field(..., description="Extracted product / commodity name or fallback filename")
    status: str = Field(..., description="COMPLIANT | POTENTIAL_VIOLATION | MANUAL_REVIEW | FAILED")
    risk_score: int = Field(0, description="Calculated non-compliance risk score (0-100)")
    violations_count: int = Field(0, description="Count of flagged statutory violations")
    average_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Mean confidence of extracted declarations")
    created_at: str = Field(..., description="ISO timestamp")
    success: bool = Field(..., description="Whether processing completed without unhandled fatal error")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class BatchInspectionResponse(BaseModel):
    batch_id: str = Field(..., description="Unique batch processing operation ID")
    total: int = Field(..., description="Total package images processed in this batch")
    compliant_count: int = Field(..., description="Total compliant packages")
    potential_violations_count: int = Field(..., description="Total packages with potential violations")
    manual_review_count: int = Field(..., description="Total packages requiring manual inspector review")
    high_risk_count: int = Field(..., description="Total packages flagged with high risk score (>= 30)")
    failed_count: int = Field(..., description="Total images that failed processing (e.g. invalid format)")
    results: List[BatchInspectionItemResult] = Field(..., description="Individual inspection outcomes for all images")
