from abc import ABC, abstractmethod
from typing import Union
from backend.app.schemas.ocr import OCRResult

class OCRProvider(ABC):
    """
    Abstract OCR Provider interface.
    Decouples package text perception from specific OCR vendors or engines.
    """

    @abstractmethod
    async def extract(
        self,
        image_input: Union[str, bytes],
        inspection_id: str = ""
    ) -> OCRResult:
        """
        Extracts visible text, confidence metrics, and spatial bounding boxes from a package image.

        :param image_input: Path to local image file or raw image bytes.
        :param inspection_id: Contextual inspection reference ID.
        :return: Structured OCRResult preserving text, confidence, bounding_box, page_number.
        """
        pass
