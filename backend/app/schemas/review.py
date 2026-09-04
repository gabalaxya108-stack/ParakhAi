from typing import Optional, Literal
from pydantic import BaseModel, Field

ReviewDecisionType = Literal[
    "CONFIRM_FINDING",
    "REJECT_FINDING",
    "REQUEST_MANUAL_VERIFICATION",
    "MARK_NOT_APPLICABLE"
]

class ReviewSubmissionRequest(BaseModel):
    decision: ReviewDecisionType = Field(
        ...,
        description="Inspector review decision: CONFIRM_FINDING, REJECT_FINDING, REQUEST_MANUAL_VERIFICATION, MARK_NOT_APPLICABLE"
    )
    comment: Optional[str] = Field(
        None,
        description="Official review comment or statutory rationale provided by inspector"
    )
    reviewer: Optional[str] = Field(
        "inspector_lm",
        description="Inspector identity submitting the review"
    )

class ReviewRecordResponse(BaseModel):
    review_id: int = Field(..., description="Unique review record identifier")
    inspection_id: str = Field(..., description="Target inspection identifier")
    reviewer: str = Field(..., description="Inspector username / credentials")
    decision: str = Field(..., description="Human review determination")
    decision_label: str = Field(..., description="Human-readable decision label")
    comment: Optional[str] = Field(None, description="Reviewer commentary")
    timestamp: str = Field(..., description="Timestamp when decision was submitted")
    original_ai_status: str = Field(..., description="Preserved immutable AI preliminary screening status")
    original_ai_risk_score: int = Field(..., description="Preserved immutable AI preliminary risk score")
