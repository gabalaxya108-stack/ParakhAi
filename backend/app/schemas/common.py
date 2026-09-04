from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    """
    Resolution-independent normalized bounding box in range [0.0, 1.0].
    ymin, xmin, ymax, xmax represent relative coordinates of the image.
    """
    ymin: float = Field(..., ge=0.0, le=1.0, description="Top normalized coordinate")
    xmin: float = Field(..., ge=0.0, le=1.0, description="Left normalized coordinate")
    ymax: float = Field(..., ge=0.0, le=1.0, description="Bottom normalized coordinate")
    xmax: float = Field(..., ge=0.0, le=1.0, description="Right normalized coordinate")
    polygon: Optional[List[List[float]]] = Field(None, description="Four-point polygon [[x1,y1],...]")
    label: Optional[str] = Field(None, description="Field label or indicator")
    estimated_font_height_mm: Optional[float] = Field(None, description="Estimated font height in mm based on PDP DPI")

    def to_pixel_box(self, img_width: int, img_height: int) -> dict:
        return {
            "x": int(self.xmin * img_width),
            "y": int(self.ymin * img_height),
            "w": int((self.xmax - self.xmin) * img_width),
            "h": int((self.ymax - self.ymin) * img_height)
        }
