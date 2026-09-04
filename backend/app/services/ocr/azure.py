import time
import io
from typing import Union
from PIL import Image
import httpx
from backend.app.services.ocr.base import OCRProvider
from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox, NormalizedBoundingBox
from backend.app.core.config import settings
from backend.app.core.errors import AppException

class AzureVisionOCRProvider(OCRProvider):
    """
    Azure AI Vision (Computer Vision 3.2 / 4.0 Read API) integration.
    """

    def __init__(self, endpoint: str = None, api_key: str = None):
        self.endpoint = (endpoint or os.getenv("AZURE_VISION_ENDPOINT", "")).rstrip("/")
        self.api_key = api_key or os.getenv("AZURE_VISION_KEY", "")

    async def extract(
        self,
        image_input: Union[str, bytes],
        inspection_id: str = ""
    ) -> OCRResult:
        if not self.endpoint or not self.api_key:
            raise AppException(
                message="Azure Vision credentials not configured (AZURE_VISION_ENDPOINT / AZURE_VISION_KEY).",
                error_code="OCR_CONFIG_ERROR",
                status_code=500
            )

        start_time = time.time()

        if isinstance(image_input, bytes):
            image_bytes = image_input
            img = Image.open(io.BytesIO(image_bytes))
        else:
            with open(image_input, "rb") as f:
                image_bytes = f.read()
            img = Image.open(image_input)

        img_w, img_h = img.size

        # In a real Azure setup, call Azure Computer Vision Read API
        # For now, if called without mock fallback, structure the request
        url = f"{self.endpoint}/vision/v3.2/read/analyze"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, content=image_bytes)
            if resp.status_code != 202:
                raise AppException(
                    message=f"Azure Vision OCR request failed: {resp.text}",
                    error_code="AZURE_OCR_ERROR",
                    status_code=502
                )
            
            # Poll operation-location...
            # (Truncated standard polling loop for Azure Read API)

        processing_time = round((time.time() - start_time) * 1000, 2)
        return OCRResult(
            inspection_id=inspection_id,
            full_text="",
            blocks=[],
            total_blocks=0,
            image_width=img_w,
            image_height=img_h,
            provider="azure_vision",
            processing_time_ms=processing_time
        )
