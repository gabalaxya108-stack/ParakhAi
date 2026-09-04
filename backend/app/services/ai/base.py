from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.app.schemas.extraction import ExtractionResult

class BaseVisionProvider(ABC):
    @abstractmethod
    async def extract_declarations(
        self,
        image_path: str,
        commodity_category: str = "Food & Beverages",
        pdp_area_sq_cm: float = 240.0,
        mm_per_pixel: float = 0.15
    ) -> ExtractionResult:
        """
        Extracts raw declarations and normalized attributes from the packaging image.
        Must NOT perform compliance checks. Only perception, OCR transcription, and spatial grounding.
        """
        pass
