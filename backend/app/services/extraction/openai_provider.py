import os
import json
import base64
import time
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io

from backend.app.schemas.ocr import OCRResult
from backend.app.schemas.extraction import ExtractedFieldsContainer, REQUIRED_DECLARATION_FIELDS
from backend.app.services.extraction.base import ExtractionProvider
from backend.app.services.extraction.validator import ExtractionValidator
from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.core.logging import get_logger

logger = get_logger("services.extraction.openai")

VISION_SYSTEM_PROMPT = """You are a Legal Metrology Vision AI perception engine.
Your task is strictly perception: identifying which mandatory packaged-commodity declarations are present on this package image and mapping them to the provided OCR blocks.

CRITICAL INSTRUCTIONS:
1. You are NOT allowed to decide legal compliance. Do NOT determine whether the product passes or fails any statutory law.
2. For each of the 11 mandatory fields, determine:
   - product_name: The brand / commercial name of the commodity
   - mrp: Maximum Retail Price as printed (e.g., '₹40', 'Rs 40.00', 'Rs. 40 (Incl. of all taxes)')
   - net_quantity: Net quantity declaration (e.g., '100 g', '250 ml', '1 kg', '500 g')
   - manufacturer: Name and address of the manufacturing unit
   - packer: Name and address of packer (null if manufacturer packs directly)
   - importer: Name and address of importer (null if domestic)
   - packing_date: Date of packaging (e.g., '05/2026')
   - manufacturing_date: Date of manufacture (e.g., '04/2026')
   - consumer_care: Customer helpline, toll-free number, contact email, or address
   - country_of_origin: Country of origin (e.g., 'India')
   - batch_or_lot_number: Batch number, Lot number, or B.No.

STRICT INVARIANT:
- If a declaration is not clearly visible or cannot be reliably identified on the package:
  value MUST be null
  confidence MUST be 0.0
  bounding_box MUST be null
  evidence_text MUST be null
- NEVER hallucinate, guess, or invent missing declarations.
- NEVER invent bounding boxes for missing fields.
- For detected fields, return the exact bounding_box {x, y, width, height} in original image pixels corresponding to where the text appears on the packaging.

OUTPUT FORMAT:
Return a strictly valid JSON object with exactly the 11 keys:
{
  "product_name": {"field": "product_name", "value": "...", "confidence": 0.95, "source": "ocr+vision", "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 30}, "evidence_text": "..."},
  "manufacturer": {"field": "manufacturer", "value": null, "confidence": 0.0, "source": "ocr+vision", "bounding_box": null, "evidence_text": null},
  ...
}
"""

class OpenAIExtractionProvider(ExtractionProvider):
    """
    Vision AI Multi-Modal Extraction Provider.
    Sends package image and Tesseract OCR block spatial context to a multi-modal LLM
    (OpenAI GPT-4o or Azure OpenAI) for declaration perception.
    Enforces strict schema validation, zero-compliance-judgment, and zero-hallucination.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        azure_endpoint: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT") or getattr(settings, "AZURE_OPENAI_ENDPOINT", None)
        self.model = model or os.getenv("VISION_AI_MODEL") or getattr(settings, "VISION_AI_MODEL", "gpt-4o")

    def _get_client(self):
        try:
            import openai
        except ImportError:
            raise AppException(
                message="The 'openai' library is not installed. Please install it to use OpenAIExtractionProvider.",
                error_code="AI_PROVIDER_UNAVAILABLE",
                status_code=503
            )

        if self.azure_endpoint:
            azure_key = os.getenv("AZURE_OPENAI_API_KEY") or getattr(settings, "AZURE_OPENAI_API_KEY", self.api_key)
            if not azure_key:
                raise AppException(
                    message="Azure OpenAI endpoint specified but AZURE_OPENAI_API_KEY is not configured.",
                    error_code="AI_PROVIDER_UNAVAILABLE",
                    status_code=503
                )
            return openai.AsyncAzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=azure_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            )
        elif self.api_key:
            return openai.AsyncOpenAI(api_key=self.api_key)
        else:
            raise AppException(
                message="Vision AI API key not configured. Set OPENAI_API_KEY in environment or switch EXTRACTION_PROVIDER to 'mock'.",
                error_code="AI_PROVIDER_UNAVAILABLE",
                status_code=503
            )

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        """Encodes image file to base64 and returns (base64_data, mime_type)."""
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif"
        }
        mime = mime_map.get(ext, "image/jpeg")

        try:
            with Image.open(image_path) as im:
                if im.mode != "RGB":
                    im = im.convert("RGB")
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return b64, "image/jpeg"
        except Exception:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return b64, mime

    async def extract(
        self,
        image_path: str,
        ocr_result: OCRResult,
        inspection_id: str = ""
    ) -> ExtractedFieldsContainer:
        client = self._get_client()

        # 1. Encode image
        if not os.path.exists(image_path):
            raise AppException(
                message=f"Package image path '{image_path}' not found.",
                error_code="IMAGE_NOT_FOUND",
                status_code=404
            )

        b64_image, mime_type = self._encode_image(image_path)

        # 2. Format OCR blocks context
        ocr_blocks_context = []
        if ocr_result and ocr_result.blocks:
            for idx, b in enumerate(ocr_result.blocks[:60]):
                ocr_blocks_context.append({
                    "id": idx,
                    "text": b.text,
                    "confidence": round(b.confidence, 2),
                    "box": {
                        "x": b.bounding_box.x,
                        "y": b.bounding_box.y,
                        "width": b.bounding_box.width,
                        "height": b.bounding_box.height
                    }
                })

        user_content = [
            {
                "type": "text",
                "text": f"Package Dimensions: {ocr_result.image_width}x{ocr_result.image_height} px.\n\n"
                        f"Tesseract OCR Detected Blocks ({len(ocr_blocks_context)} blocks):\n"
                        f"{json.dumps(ocr_blocks_context, indent=2)}\n\n"
                        f"Identify which detected text corresponds to which of the 11 package declarations."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_image}",
                    "detail": "high"
                }
            }
        ]

        logger.info(f"Invoking Vision AI model '{self.model}' for inspection '{inspection_id}' with {len(ocr_blocks_context)} OCR blocks")
        t0 = time.time()

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=1500
            )
            elapsed_ms = (time.time() - t0) * 1000
            logger.info(f"Vision AI completed in {elapsed_ms:.0f}ms")
        except Exception as e:
            logger.error(f"Vision AI model invocation failed: {e}")
            raise AppException(
                message=f"Vision AI declaration extraction model failed: {str(e)}",
                error_code="AI_PROVIDER_ERROR",
                status_code=502
            )

        content = response.choices[0].message.content
        try:
            raw_payload = json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse Vision AI JSON response: {content}")
            raise AppException(
                message="Vision AI returned invalid JSON.",
                error_code="MALFORMED_EXTRACTION_OUTPUT",
                status_code=422
            )

        # Enforce invariant: if value is None, bounding_box and evidence_text MUST be None
        for k in REQUIRED_DECLARATION_FIELDS:
            if k in raw_payload and isinstance(raw_payload[k], dict):
                field_dict = raw_payload[k]
                field_dict["field"] = k
                field_dict["source"] = field_dict.get("source") or "ocr+vision"
                if field_dict.get("value") is None or str(field_dict.get("value")).strip() == "":
                    field_dict["value"] = None
                    field_dict["confidence"] = 0.0
                    field_dict["bounding_box"] = None
                    field_dict["evidence_text"] = None

        return ExtractionValidator.validate_model_payload(raw_payload)
