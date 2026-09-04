import os
import io
import time
import json
import base64
import re
import asyncio
from typing import Optional, Dict, Any, Tuple
from PIL import Image

from backend.app.core.config import settings
from backend.app.schemas.ocr import OCRResult, PixelBoundingBox
from backend.app.schemas.extraction import (
    ExtractedFieldsContainer,
    FieldExtractionResult,
    REQUIRED_DECLARATION_FIELDS
)
from backend.app.services.extraction.base import ExtractionProvider
from backend.app.services.extraction.validator import ExtractionValidator
from backend.app.core.logging import get_logger
from backend.app.core.errors import AppException

logger = get_logger("services.extraction.groq_provider")

GROQ_VISION_SYSTEM_PROMPT = """You are a package label declaration extractor for Indian Legal Metrology regulatory inspections.
Inspect the packaging image and extract the 11 statutory declarations into a compact JSON object with string values (or null if not present):
{
  "product_name": string or null,
  "manufacturer": string or null (name and complete address),
  "packer": string or null (name and address, or null),
  "importer": string or null (name and address, or null),
  "net_quantity": string or null (e.g. "140 g"),
  "mrp": string or null (exact Maximum Retail Price declaration including currency and tax phrase, e.g. "Rs. 60.00 (Inclusive of all taxes)"),
  "unit_sale_price": string or null (e.g. "Rs. 0.30 per g"),
  "packing_date": string or null,
  "manufacturing_date": string or null,
  "consumer_care": string or null (email, phone, or address),
  "country_of_origin": string or null (e.g. "India"),
  "batch_or_lot_number": string or null
}

Do not determine legal compliance. If a declaration is not visibly present on this package label, set value to null.
Never hallucinate or guess missing values.
Output strictly the JSON object."""

class GroqQwenVisionProvider(ExtractionProvider):
    """
    Primary Vision Extraction Provider using Groq's Vision API with Qwen Vision.
    Performs multi-modal perception on high-resolution packaging imagery.
    
    Adheres strictly to:
    - Model selection is configurable via GROQ_VISION_MODEL (default: qwen/qwen3.6-27b)
    - Zero compliance judgment (perception only)
    - Zero hallucination of missing values
    - Preserves bounding boxes and physical text evidence
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY") or getattr(settings, "GROK_API_KEY", None) or getattr(settings, "GROQ_API_KEY", None)
        self.model = model or os.getenv("GROQ_VISION_MODEL") or getattr(settings, "GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

    def _get_client(self):
        if not self.api_key or not self.api_key.strip():
            raise AppException(
                message="GROQ_API_KEY is not configured in environment or .env.",
                error_code="GROQ_API_KEY_MISSING",
                status_code=503
            )

        try:
            from groq import AsyncGroq
            return AsyncGroq(api_key=self.api_key.strip())
        except ImportError:
            raise AppException(
                message="The 'groq' Python package is not installed.",
                error_code="GROQ_PACKAGE_MISSING",
                status_code=503
            )

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        """Encodes image to base64 JPEG format with dimension bounds."""
        if not os.path.exists(image_path):
            raise AppException(
                message=f"Image file '{image_path}' not found.",
                error_code="IMAGE_FILE_NOT_FOUND",
                status_code=404
            )

        try:
            with Image.open(image_path) as im:
                if im.mode != "RGB":
                    im = im.convert("RGB")
                
                # Resize if excessively large to avoid Groq payload limits while preserving readability
                max_dim = 2048
                if max(im.width, im.height) > max_dim:
                    im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=90)
                b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                return b64_str, "image/jpeg"
        except Exception as e:
            with open(image_path, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
                return b64_str, "image/jpeg"

    async def extract(
        self,
        image_path: str,
        ocr_result: OCRResult,
        inspection_id: str = ""
    ) -> ExtractedFieldsContainer:
        """
        Executes Vision AI extraction using Groq Qwen Vision.
        """
        client = self._get_client()
        b64_image, mime_type = self._encode_image(image_path)

        # Build OCR context snippet (first 50 blocks) to assist spatial disambiguation
        ocr_snippets = []
        if ocr_result and ocr_result.blocks:
            for b in ocr_result.blocks[:50]:
                if b.text and len(b.text.strip()) > 1:
                    ocr_snippets.append({
                        "text": b.text.strip(),
                        "box": {
                            "x": b.bounding_box.x,
                            "y": b.bounding_box.y,
                            "width": b.bounding_box.width,
                            "height": b.bounding_box.height
                        }
                    })

        user_prompt_text = "Examine the attached packaging label image carefully. Extract all mandatory package declarations into the required JSON object."

        messages = [
            {"role": "system", "content": GROQ_VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_image}"
                        }
                    }
                ]
            }
        ]

        logger.info(
            f"Invoking Groq Vision model '{self.model}' for inspection '{inspection_id}'"
        )
        t0 = time.time()

        response = None
        last_err = None
        candidate_models = []
        for m in [self.model, "qwen/qwen3.8-27b", "qwen/qwen3.6-27b"]:
            if m and m not in candidate_models:
                candidate_models.append(m)

        for candidate_model in candidate_models:
            try:
                logger.info(f"Invoking Groq Vision model '{candidate_model}' for inspection '{inspection_id}'")
                response = await client.chat.completions.create(
                    model=candidate_model,
                    messages=messages,
                    extra_body={"reasoning_format": "hidden"},
                    temperature=0.0,
                    max_tokens=450,
                    timeout=12.0
                )
                self.model = candidate_model
                break
            except Exception as e:
                logger.warning(f"Groq Vision with '{candidate_model}' failed: {e}. Trying next model if available...")
                last_err = e
                continue

        if not response:
            logger.error(f"All Groq Vision models failed for inspection '{inspection_id}': {last_err}")
            raise AppException(
                message=f"Groq Vision extraction failed: {str(last_err)}",
                error_code="GROQ_VISION_API_ERROR",
                status_code=502
            )

        if not response:
            raise AppException(
                message="Groq Vision failed to produce a response.",
                error_code="GROQ_VISION_EMPTY_RESPONSE",
                status_code=502
            )

        elapsed_ms = (time.time() - t0) * 1000
        usage_info = getattr(response, "usage", None)
        tokens_str = f"prompt_tokens={usage_info.prompt_tokens}, completion_tokens={usage_info.completion_tokens}" if usage_info else "usage=n/a"
        logger.info(
            f"Groq Vision '{self.model}' completed for '{inspection_id}' in {elapsed_ms:.0f}ms ({tokens_str})"
        )

        content = response.choices[0].message.content or ""
        # Strip reasoning thinking block (complete or truncated)
        clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if "<think>" in clean_content:
            clean_content = re.sub(r"<think>.*", "", clean_content, flags=re.DOTALL).strip()

        # Handle markdown code blocks
        if "```" in clean_content:
            fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_content, flags=re.DOTALL)
            if fence_match:
                clean_content = fence_match.group(1)
            else:
                clean_content = clean_content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        
        if not clean_content.startswith("{"):
            brace_match = re.search(r"(\{.*\})", clean_content, flags=re.DOTALL)
            if brace_match:
                clean_content = brace_match.group(1)
            else:
                # Last ditch: check if full content had a JSON block
                full_brace = re.search(r"(\{[\s\S]*\})", content)
                if full_brace:
                    clean_content = full_brace.group(1)

        try:
            raw_payload = json.loads(clean_content)
        except Exception as e:
            logger.error(f"Failed to parse Groq Vision JSON response: {clean_content}")
            raise AppException(
                message="Groq Vision returned invalid JSON payload.",
                error_code="MALFORMED_VISION_OUTPUT",
                status_code=422
            )

        # Normalize and enforce invariants
        normalized: Dict[str, Any] = {}
        for field_name in REQUIRED_DECLARATION_FIELDS:
            raw_field = raw_payload.get(field_name)
            if isinstance(raw_field, dict):
                val = raw_field.get("value")
                conf = float(raw_field.get("confidence", 0.95 if val else 0.0))
                ev = raw_field.get("evidence_text") or (str(val) if val else None)
                bbox_dict = raw_field.get("bounding_box")
            else:
                val = raw_field
                conf = 0.95 if val else 0.0
                ev = str(val) if val else None
                bbox_dict = None
            
            # Treat empty strings or 'null'/'not_detected' as None
            if val is not None and str(val).strip().lower() in ("", "null", "none", "not_detected", "n/a", "not detected"):
                val = None

            if not val:
                conf = 0.0

            bbox = None
            if bbox_dict and isinstance(bbox_dict, dict) and val:
                try:
                    bbox = PixelBoundingBox(
                        x=int(bbox_dict.get("x", 0)),
                        y=int(bbox_dict.get("y", 0)),
                        width=int(bbox_dict.get("width", 50)),
                        height=int(bbox_dict.get("height", 20))
                    )
                except Exception:
                    bbox = None

            # Spatial back-projection: Match against Tesseract OCR blocks
            if not bbox and val and ocr_result and ocr_result.blocks:
                val_str = str(val).strip().lower()
                best_block = None
                for b in ocr_result.blocks:
                    if not b.bounding_box or not b.text:
                        continue
                    b_txt = b.text.strip().lower()
                    if len(b_txt) >= 2 and (b_txt in val_str or val_str in b_txt):
                        best_block = b
                        break
                if not best_block:
                    tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", val_str) if len(t) >= 2]
                    max_overlap = 0
                    for b in ocr_result.blocks:
                        if not b.bounding_box or not b.text:
                            continue
                        b_txt = b.text.strip().lower()
                        overlap = sum(1 for t in tokens if t in b_txt)
                        if overlap > max_overlap:
                            max_overlap = overlap
                            best_block = b
                if best_block and best_block.bounding_box:
                    bbox = best_block.bounding_box

            ev_text = ev
            if val and not ev_text:
                ev_text = str(val)

            status = "FOUND" if val else "NOT_FOUND"

            normalized[field_name] = {
                "field": field_name,
                "value": str(val).strip() if val else None,
                "confidence": max(0.0, min(1.0, conf)),
                "source": "qwen_vision",
                "bounding_box": bbox.model_dump() if bbox else None,
                "evidence_text": ev_text,
                "status": status,
                "raw_value": str(val) if val else None
            }

        return ExtractionValidator.validate_model_payload(normalized)
