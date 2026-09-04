from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class PixelBoundingBox(BaseModel):
    x: int = Field(..., description="X coordinate of top-left corner in pixels")
    y: int = Field(..., description="Y coordinate of top-left corner in pixels")
    width: int = Field(..., description="Width of bounding box in pixels")
    height: int = Field(..., description="Height of bounding box in pixels")

    model_config = ConfigDict(from_attributes=True)

class NormalizedBoundingBox(BaseModel):
    ymin: float = Field(..., ge=0.0, le=1.0, description="Top normalized coordinate (0.0 to 1.0)")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Left normalized coordinate (0.0 to 1.0)")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Bottom normalized coordinate (0.0 to 1.0)")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Right normalized coordinate (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)

class OCRBlock(BaseModel):
    text: str = Field(..., description="Detected text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    bounding_box: PixelBoundingBox = Field(..., description="Bounding box in pixel coordinates")
    normalized_box: Optional[NormalizedBoundingBox] = Field(None, description="Bounding box in normalized coordinates")
    page_number: int = Field(default=1, description="Page or image index")
    source_image_variant: Optional[str] = Field(default="original", description="Image variant that produced this block")
    psm_mode: Optional[int] = Field(default=3, description="Tesseract Page Segmentation Mode used")
    region: Optional[str] = Field(default="full", description="Image region (full, header, statutory_left, bottom_panel)")

    model_config = ConfigDict(from_attributes=True)

class OCRResult(BaseModel):
    inspection_id: str = Field(..., description="Unique inspection identifier")
    full_text: str = Field(..., description="Full combined text extracted from the package image")
    blocks: List[OCRBlock] = Field(default_factory=list, description="List of recognized text blocks with bounding boxes")
    total_blocks: int = Field(..., description="Total count of recognized text blocks")
    image_width: int = Field(..., description="Original image width in pixels")
    image_height: int = Field(..., description="Original image height in pixels")
    provider: str = Field(..., description="OCR engine provider used (e.g. tesseract, mock, azure_vision)")
    version: Optional[str] = Field(default="5.5.3", description="OCR engine version")
    languages: Optional[List[str]] = Field(default_factory=lambda: ["eng", "hin"], description="Configured OCR languages")
    processing_time_ms: float = Field(..., description="OCR extraction duration in milliseconds")
    results: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Structured OCR results for external API clients")
    quality_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Image quality analysis metrics")

    model_config = ConfigDict(from_attributes=True)
