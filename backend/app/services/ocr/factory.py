from backend.app.core.config import settings
from backend.app.services.ocr.base import OCRProvider
from backend.app.services.ocr.mock import MockOCRProvider
from backend.app.core.logging import get_logger

logger = get_logger("services.ocr.factory")

def get_ocr_provider(provider_name: str = None) -> OCRProvider:
    name = (provider_name or settings.OCR_PROVIDER).lower().strip()

    if name == "mock":
        return MockOCRProvider()
    elif name == "tesseract":
        from backend.app.services.ocr.tesseract import TesseractOCRProvider
        return TesseractOCRProvider()
    elif name in ["azure", "azure_vision"]:
        from backend.app.services.ocr.azure import AzureVisionOCRProvider
        return AzureVisionOCRProvider()
    else:
        logger.warning(f"Unrecognized OCR provider '{name}'. Defaulting to 'mock' provider.")
        return MockOCRProvider()
