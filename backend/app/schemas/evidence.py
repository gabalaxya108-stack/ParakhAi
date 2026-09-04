from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.ocr import PixelBoundingBox

class EvidenceModel(BaseModel):
    evidence_id: str = Field(..., description="Unique evidence tracking identifier")
    inspection_id: str = Field(..., description="Contextual inspection identifier")
    rule_id: str = Field(..., description="Associated statutory rule ID (e.g. LM-MRP-001)")
    type: str = Field(
        ...,
        description="ABSENCE | INCORRECT_DECLARATION | UNCERTAIN | DETECTED_DECLARATION"
    )
    image_id: str = Field(..., description="Reference to the analyzed image asset")
    bounding_box: Optional[PixelBoundingBox] = Field(
        None,
        description="Pixel bounding box coordinates on package label, or null if evidence of absence/unavailable"
    )
    detected_text: Optional[str] = Field(None, description="Actual OCR/Vision text found in the evidence region, or null")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Perception confidence metric")
    explanation: str = Field(..., description="Traceable explanation connecting the statutory check to the image region")
    evidence_available: bool = Field(..., description="Whether a localized image region is available")

    model_config = ConfigDict(from_attributes=True)

class EvidenceSummary(BaseModel):
    detected_count: int = Field(0)
    incorrect_count: int = Field(0)
    absence_count: int = Field(0)
    uncertain_count: int = Field(0)

class EvidenceListResponse(BaseModel):
    inspection_id: str = Field(..., description="Contextual inspection identifier")
    total: int = Field(..., description="Total evidence items generated")
    evidence: List[EvidenceModel] = Field(..., description="List of evidence traces")
    summary: EvidenceSummary = Field(..., description="Evidence breakdown by classification type")

    model_config = ConfigDict(from_attributes=True)
