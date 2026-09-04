from abc import ABC, abstractmethod
from backend.app.schemas.ocr import OCRResult
from backend.app.schemas.extraction import ExtractedFieldsContainer

class ExtractionProvider(ABC):
    """
    Abstract declaration extraction provider.
    Its sole duty is perception: extracting printed declarations and bounding boxes.
    It does NOT evaluate legal compliance.
    """

    @abstractmethod
    async def extract(
        self,
        image_path: str,
        ocr_result: OCRResult,
        inspection_id: str = ""
    ) -> ExtractedFieldsContainer:
        """
        Extracts the 11 mandatory declaration fields from the package image and OCR output.
        If a field is not found with high confidence, value MUST be null.
        """
        pass

# Alias for modular vision provider abstraction
VisionExtractionProvider = ExtractionProvider
