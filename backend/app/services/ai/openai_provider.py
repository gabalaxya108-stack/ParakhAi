import os
import json
import base64
import uuid
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from backend.app.core.config import settings
from backend.app.services.ai.base import BaseVisionProvider
from backend.app.schemas.extraction import (
    ExtractionResult,
    ExtractedDeclarationDTO,
    DeclarationType
)
from backend.app.schemas.common import BoundingBox

EXTRACTION_SYSTEM_PROMPT = """You are an expert Legal Metrology OCR and Label Perception System.
Extract and ground all mandatory declarations printed on the package.
STRICT RULES:
1. Do NOT evaluate compliance or legality. Only extract and transcribe visible text.
2. Provide resolution-independent normalized bounding boxes: ymin, xmin, ymax, xmax (0.0 to 1.0).
3. Return valid JSON adhering strictly to the required schema.
"""

class OpenAIVisionProvider(BaseVisionProvider):
    def __init__(self):
        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
            self.client = AsyncOpenAI(
                base_url=f"{settings.AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT_NAME}",
                api_key=settings.AZURE_OPENAI_API_KEY,
                default_query={"api-version": "2024-02-15-preview"}
            )
            self.model = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or "sk-dummy")
            self.model = "gpt-4o"

    async def extract_declarations(
        self,
        image_path: str,
        commodity_category: str = "Food & Beverages",
        pdp_area_sq_cm: float = 240.0,
        mm_per_pixel: float = 0.15
    ) -> ExtractionResult:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Extract all legal declarations from this {commodity_category} packaging."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=2000
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        
        declarations = []
        for item in data.get("declarations", []):
            try:
                dtype = DeclarationType(item.get("type", "GENERIC_NAME"))
            except ValueError:
                dtype = DeclarationType.GENERIC_NAME

            raw_box = item.get("bounding_box", {})
            bbox = BoundingBox(
                ymin=float(raw_box.get("ymin", 0.0)),
                xmin=float(raw_box.get("xmin", 0.0)),
                ymax=float(raw_box.get("ymax", 1.0)),
                xmax=float(raw_box.get("xmax", 1.0)),
                label=item.get("type")
            )
            declarations.append(
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=dtype,
                    raw_text=item.get("raw_text", ""),
                    normalized_value=item.get("normalized_value", item.get("raw_text")),
                    parsed_attributes=item.get("parsed_attributes", {}),
                    confidence=float(item.get("confidence", 0.90)),
                    bounding_box=bbox
                )
            )

        return ExtractionResult(
            product_name=data.get("product_name"),
            brand_name=data.get("brand_name"),
            commodity_category=commodity_category,
            batch_lot_number=data.get("batch_lot_number"),
            declarations=declarations,
            source_engine=f"OpenAI-{self.model}"
        )
