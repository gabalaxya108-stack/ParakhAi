from pydantic import BaseModel, Field, ConfigDict

class InspectionUploadResponse(BaseModel):
    inspection_id: str = Field(..., description="Unique generated inspection identifier")
    filename: str = Field(..., description="Original filename of the uploaded package image")
    mime_type: str = Field(..., description="Validated MIME type (image/jpeg, image/png, image/tiff)")
    file_size: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="UTC ISO-8601 creation timestamp")
    image_location: str = Field(..., description="Storage key / location reference")
    image_url: str = Field(..., description="Public endpoint URL for the stored image")
    status: str = Field("UPLOADED", description="Inspection lifecycle status")

    model_config = ConfigDict(from_attributes=True)
