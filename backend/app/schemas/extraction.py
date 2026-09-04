from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.schemas.ocr import PixelBoundingBox

REQUIRED_DECLARATION_FIELDS = [
    "product_name",
    "manufacturer",
    "packer",
    "importer",
    "net_quantity",
    "mrp",
    "packing_date",
    "manufacturing_date",
    "consumer_care",
    "country_of_origin",
    "batch_or_lot_number"
]

class CandidateObservation(BaseModel):
    """An individual extraction candidate observation from Tesseract or Qwen Vision."""
    value: Optional[str] = None
    source: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence_text: Optional[str] = None
    bounding_box: Optional[PixelBoundingBox] = None

    model_config = ConfigDict(from_attributes=True)

class ReconciliationDetail(BaseModel):
    """Forensic reconciliation between Tesseract OCR and Qwen Vision."""
    field: str
    candidates: List[CandidateObservation] = []
    resolution: str = "single_source"  # "agreement" | "disagreement" | "single_source" | "both_absent"
    conflict_detected: bool = False
    reconciliation_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FieldExtractionResult(BaseModel):
    """
    Extracted declaration field with spatial grounding, evidence, and confidence.
    If the field is not confidently detected or fails quality checks:
    - value = null
    - status = 'NOT_FOUND' or 'UNCLEAR'
    """
    field: str = Field(..., description="Canonical declaration name (e.g. mrp, net_quantity)")
    value: Optional[str] = Field(None, description="Clean textual declaration value as printed, or null if missing/unclear")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    source: str = Field("ocr+vision", description="Perception source: 'tesseract', 'qwen_vision', or 'qwen_vision+tesseract'")
    bounding_box: Optional[PixelBoundingBox] = Field(None, description="Pixel-level bounding box on the package")
    evidence_text: Optional[str] = Field(None, description="Exact raw text snippet from packaging serving as evidence")
    status: Optional[str] = Field("FOUND", description="Declaration detection status: 'FOUND', 'NOT_FOUND', 'UNCLEAR'")
    raw_value: Optional[str] = Field(None, description="Raw unnormalized OCR snippet before quality filtering")
    conflict_detected: Optional[bool] = Field(False, description="True if Tesseract and Qwen Vision reported conflicting candidate values")
    candidates: Optional[List[CandidateObservation]] = Field(None, description="Candidate values from participating perception engines")

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("field")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        if v not in REQUIRED_DECLARATION_FIELDS:
            raise ValueError(f"Field '{v}' is not a recognized Legal Metrology declaration. Allowed fields: {REQUIRED_DECLARATION_FIELDS}")
        return v

class ExtractedFieldsContainer(BaseModel):
    """
    Strict container holding all 11 mandatory declaration fields.
    Forbids extra, unsupported, or hallucinated fields.
    """
    product_name: FieldExtractionResult
    manufacturer: FieldExtractionResult
    packer: FieldExtractionResult
    importer: FieldExtractionResult
    net_quantity: FieldExtractionResult
    mrp: FieldExtractionResult
    packing_date: FieldExtractionResult
    manufacturing_date: FieldExtractionResult
    consumer_care: FieldExtractionResult
    country_of_origin: FieldExtractionResult
    batch_or_lot_number: FieldExtractionResult

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class ExtractionResponse(BaseModel):
    """
    Structured API response returned by POST /api/v1/inspections/{inspection_id}/extract
    """
    inspection_id: str = Field(..., description="Unique inspection identifier")
    fields: ExtractedFieldsContainer = Field(..., description="Container of all 11 declaration fields")
    extracted_fields_count: int = Field(..., description="Number of fields detected with non-null values")
    missing_fields_count: int = Field(..., description="Number of fields where value is null")
    provider: str = Field(..., description="Extraction AI/Heuristic provider used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    vision_provider: Optional[str] = Field(None, description="Vision model identifier if invoked (e.g. qwen/qwen3.6-27b)")
    vision_status: Optional[str] = Field("active", description="Vision extraction status: 'active', 'fallback_tesseract', 'unavailable'")
    preprocessing_status: Optional[str] = Field("processed", description="Image preprocessing outcome: 'processed' or 'fallback_original'")
    reconciliation: Optional[Dict[str, ReconciliationDetail]] = Field(None, description="Per-field reconciliation between Tesseract and Qwen")

    model_config = ConfigDict(from_attributes=True)

class InspectionDebugDossierResponse(BaseModel):
    """
    Complete developer/statutory inspection dossier for Section 19 hackathon audit.
    """
    inspection_id: str
    original_image_url: str
    processed_image_url: Optional[str] = None
    preprocessing_status: str = "processed"
    preprocessing_metadata: Dict[str, Any] = {}
    tesseract: Dict[str, Any] = {}
    vision: Dict[str, Any] = {}
    reconciliation: Dict[str, ReconciliationDetail] = {}
    rule_engine_input: Dict[str, Any] = {}
    rule_engine_output: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)
