import json
import uuid
from backend.app.core.config import settings
from backend.app.services.ai.base import BaseVisionProvider
from backend.app.schemas.extraction import (
    ExtractionResult,
    ExtractedDeclarationDTO,
    DeclarationType
)
from backend.app.schemas.common import BoundingBox

class GeminiVisionProvider(BaseVisionProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def extract_declarations(
        self,
        image_path: str,
        commodity_category: str = "Food & Beverages",
        pdp_area_sq_cm: float = 240.0,
        mm_per_pixel: float = 0.15
    ) -> ExtractionResult:
        from PIL import Image
        img = Image.open(image_path)
        prompt = """Extract all package declarations as JSON with keys: product_name, brand_name, declarations: [{type, raw_text, normalized_value, confidence, bounding_box: {ymin, xmin, ymax, xmax}}]. Valid types: NAME_AND_ADDRESS, GENERIC_NAME, NET_QUANTITY, RETAIL_SALE_PRICE, UNIT_SALE_PRICE, DATE_OF_MANUFACTURE, EXPIRY_DATE, CONSUMER_CARE, COUNTRY_OF_ORIGIN."""
        
        response = self.model.generate_content([prompt, img])
        text = response.text
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())

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
                    confidence=float(item.get("confidence", 0.92)),
                    bounding_box=bbox
                )
            )

        return ExtractionResult(
            product_name=data.get("product_name"),
            brand_name=data.get("brand_name"),
            commodity_category=commodity_category,
            declarations=declarations,
            source_engine="Google-Gemini-1.5-Flash"
        )
