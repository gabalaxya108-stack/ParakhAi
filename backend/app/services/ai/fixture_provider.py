import uuid
from typing import Dict, Any, Optional
from backend.app.services.ai.base import BaseVisionProvider
from backend.app.schemas.extraction import (
    ExtractionResult,
    ExtractedDeclarationDTO,
    DeclarationType
)
from backend.app.schemas.common import BoundingBox

class FixtureVisionProvider(BaseVisionProvider):
    """
    High-fidelity realistic perception fixture provider.
    Enables instant, offline, deterministic demonstration with real-world packaging label fixtures.
    """
    
    async def extract_declarations(
        self,
        image_path: str,
        commodity_category: str = "Food & Beverages",
        pdp_area_sq_cm: float = 240.0,
        mm_per_pixel: float = 0.15
    ) -> ExtractionResult:
        lower_path = image_path.lower()

        # Sample 2: Compliant Coffee
        if "coffee" in lower_path or "compliant" in lower_path:
            return self._get_compliant_coffee_fixture(mm_per_pixel)
        
        # Sample 3: Imported Earbuds (Missing Origin, Post-dated)
        elif "earbuds" in lower_path or "electronic" in lower_path:
            return self._get_earbuds_fixture(mm_per_pixel)

        # Sample 4: Almond Drink (Missing generic name)
        elif "almond" in lower_path or "beverage" in lower_path:
            return self._get_almond_milk_fixture(mm_per_pixel)

        # Default / Sample 1: Non-Compliant Potato Chips (Illegal 'gms', missing taxes, missing USP, font height)
        else:
            return self._get_chips_violation_fixture(mm_per_pixel)

    def _get_chips_violation_fixture(self, mm_per_pixel: float) -> ExtractionResult:
        return ExtractionResult(
            product_name="Crunchy Magic Masala Potato Chips",
            brand_name="Desi Crunch",
            commodity_category="Snack Foods",
            batch_lot_number="LOT-2026-B88",
            processing_time_ms=642.0,
            source_engine="VLM-Grounding-Engine (Simulated)",
            declarations=[
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.GENERIC_NAME,
                    raw_text="POTATO CHIPS",
                    normalized_value="Potato Chips",
                    parsed_attributes={"category": "Snacks", "type": "Fried Potato Wafers"},
                    confidence=0.98,
                    bounding_box=BoundingBox(
                        ymin=0.22, xmin=0.18, ymax=0.28, xmax=0.82,
                        label="Generic Name", estimated_font_height_mm=round(18.0 * mm_per_pixel, 2)
                    )
                ),
                # VIOLATION: Uses illegal '120 gms' instead of '120 g', numeral font too small (1.8mm)
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NET_QUANTITY,
                    raw_text="Net Wt.: 120 gms",
                    normalized_value="120 gms",
                    parsed_attributes={"amount": 120.0, "unit": "gms"},
                    confidence=0.96,
                    bounding_box=BoundingBox(
                        ymin=0.68, xmin=0.14, ymax=0.73, xmax=0.48,
                        label="Net Quantity", estimated_font_height_mm=1.80  # Below 4.0mm threshold!
                    )
                ),
                # VIOLATION: Missing "(incl. of all taxes)" clause
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.RETAIL_SALE_PRICE,
                    raw_text="MRP: ₹ 35.00",
                    normalized_value="₹ 35.00",
                    parsed_attributes={"amount": 35.0, "currency": "INR", "taxes_included": False},
                    confidence=0.95,
                    bounding_box=BoundingBox(
                        ymin=0.74, xmin=0.14, ymax=0.79, xmax=0.46,
                        label="MRP", estimated_font_height_mm=round(14.0 * mm_per_pixel, 2)
                    )
                ),
                # VIOLATION: Unit Sale Price (USP) is completely omitted despite net weight 120g > 100g
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.DATE_OF_MANUFACTURE,
                    raw_text="Pkd: 06/2026",
                    normalized_value="06/2026",
                    parsed_attributes={"month": 6, "year": 2026},
                    confidence=0.94,
                    bounding_box=BoundingBox(
                        ymin=0.80, xmin=0.14, ymax=0.85, xmax=0.45,
                        label="Packing Date", estimated_font_height_mm=round(12.0 * mm_per_pixel, 2)
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NAME_AND_ADDRESS,
                    raw_text="Mfd. by: Desi Snacks Ltd., Plot 14, Phase II, Industrial Area, Okhla, New Delhi - 110020",
                    normalized_value="Desi Snacks Ltd., Plot 14, Phase II, Industrial Area, Okhla, New Delhi - 110020",
                    parsed_attributes={"role": "Manufacturer", "pincode": "110020", "state": "Delhi"},
                    confidence=0.93,
                    bounding_box=BoundingBox(
                        ymin=0.86, xmin=0.12, ymax=0.93, xmax=0.88,
                        label="Manufacturer Details", estimated_font_height_mm=round(10.0 * mm_per_pixel, 2)
                    )
                ),
                # WARNING: Missing phone helpline, only email
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.CONSUMER_CARE,
                    raw_text="Consumer Care: feedback@desisnacks.com",
                    normalized_value="feedback@desisnacks.com",
                    parsed_attributes={"email": "feedback@desisnacks.com"},
                    confidence=0.91,
                    bounding_box=BoundingBox(
                        ymin=0.94, xmin=0.14, ymax=0.98, xmax=0.85,
                        label="Consumer Care", estimated_font_height_mm=round(9.0 * mm_per_pixel, 2)
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.COUNTRY_OF_ORIGIN,
                    raw_text="Country of Origin: India",
                    normalized_value="India",
                    parsed_attributes={"country": "India"},
                    confidence=0.97,
                    bounding_box=BoundingBox(
                        ymin=0.68, xmin=0.55, ymax=0.73, xmax=0.88,
                        label="Country of Origin", estimated_font_height_mm=round(11.0 * mm_per_pixel, 2)
                    )
                )
            ]
        )

    def _get_compliant_coffee_fixture(self, mm_per_pixel: float) -> ExtractionResult:
        return ExtractionResult(
            product_name="Single Origin Arabica Beans",
            brand_name="Artisan Hills Coffee",
            commodity_category="Beverages & Coffee",
            batch_lot_number="BATCH-AH-904",
            processing_time_ms=580.0,
            source_engine="VLM-Grounding-Engine (Simulated)",
            declarations=[
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.GENERIC_NAME,
                    raw_text="ROASTED WHOLE COFFEE BEANS",
                    normalized_value="Roasted Whole Coffee Beans",
                    parsed_attributes={"category": "Coffee"},
                    confidence=0.99,
                    bounding_box=BoundingBox(
                        ymin=0.20, xmin=0.15, ymax=0.26, xmax=0.85,
                        label="Generic Name", estimated_font_height_mm=5.2
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NET_QUANTITY,
                    raw_text="Net Weight: 250 g",
                    normalized_value="250 g",
                    parsed_attributes={"amount": 250.0, "unit": "g"},
                    confidence=0.99,
                    bounding_box=BoundingBox(
                        ymin=0.65, xmin=0.15, ymax=0.71, xmax=0.50,
                        label="Net Quantity", estimated_font_height_mm=4.80
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.RETAIL_SALE_PRICE,
                    raw_text="MRP: ₹ 450.00 (inclusive of all taxes)",
                    normalized_value="₹ 450.00 (inclusive of all taxes)",
                    parsed_attributes={"amount": 450.0, "currency": "INR", "taxes_included": True},
                    confidence=0.98,
                    bounding_box=BoundingBox(
                        ymin=0.72, xmin=0.15, ymax=0.78, xmax=0.85,
                        label="MRP", estimated_font_height_mm=4.20
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.UNIT_SALE_PRICE,
                    raw_text="Unit Sale Price: ₹ 1.80 / g",
                    normalized_value="₹ 1.80 / g",
                    parsed_attributes={"amount": 1.80, "unit": "g", "currency": "INR"},
                    confidence=0.97,
                    bounding_box=BoundingBox(
                        ymin=0.79, xmin=0.15, ymax=0.84, xmax=0.60,
                        label="Unit Sale Price", estimated_font_height_mm=4.00
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.DATE_OF_MANUFACTURE,
                    raw_text="Packed On: 07/2026",
                    normalized_value="07/2026",
                    parsed_attributes={"month": 7, "year": 2026},
                    confidence=0.97,
                    bounding_box=BoundingBox(
                        ymin=0.85, xmin=0.15, ymax=0.89, xmax=0.45,
                        label="Packing Date", estimated_font_height_mm=3.80
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NAME_AND_ADDRESS,
                    raw_text="Manufactured & Packed by: Artisan Hills Coffee Roasters Pvt. Ltd., Estate Road, Coorg, Karnataka - 571201",
                    normalized_value="Artisan Hills Coffee Roasters Pvt. Ltd., Estate Road, Coorg, Karnataka - 571201",
                    parsed_attributes={"role": "Manufacturer & Packer", "pincode": "571201"},
                    confidence=0.98,
                    bounding_box=BoundingBox(
                        ymin=0.90, xmin=0.10, ymax=0.95, xmax=0.90,
                        label="Manufacturer Details", estimated_font_height_mm=3.50
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.CONSUMER_CARE,
                    raw_text="Consumer Helpline: 1800-200-4545 | Email: support@artisancoffee.in",
                    normalized_value="1800-200-4545, support@artisancoffee.in",
                    parsed_attributes={"phone": "1800-200-4545", "email": "support@artisancoffee.in"},
                    confidence=0.97,
                    bounding_box=BoundingBox(
                        ymin=0.95, xmin=0.10, ymax=0.99, xmax=0.90,
                        label="Consumer Care", estimated_font_height_mm=3.20
                    )
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.COUNTRY_OF_ORIGIN,
                    raw_text="Country of Origin: India",
                    normalized_value="India",
                    parsed_attributes={"country": "India"},
                    confidence=0.99,
                    bounding_box=BoundingBox(
                        ymin=0.85, xmin=0.55, ymax=0.89, xmax=0.88,
                        label="Country of Origin", estimated_font_height_mm=3.80
                    )
                )
            ]
        )

    def _get_earbuds_fixture(self, mm_per_pixel: float) -> ExtractionResult:
        return ExtractionResult(
            product_name="Pro Bass Wireless ANC Earbuds",
            brand_name="SoundWave",
            commodity_category="Electronics",
            batch_lot_number="SW-EB-2026",
            processing_time_ms=610.0,
            source_engine="VLM-Grounding-Engine (Simulated)",
            declarations=[
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.GENERIC_NAME,
                    raw_text="TRUE WIRELESS STEREO EARBUDS",
                    normalized_value="True Wireless Stereo Earbuds",
                    parsed_attributes={"category": "Audio"},
                    confidence=0.98,
                    bounding_box=BoundingBox(ymin=0.25, xmin=0.15, ymax=0.32, xmax=0.85, label="Generic Name")
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NET_QUANTITY,
                    raw_text="Net Quantity: 1 N (1 Pair Earbuds, 1 Charging Case)",
                    normalized_value="1 N",
                    parsed_attributes={"amount": 1.0, "unit": "N"},
                    confidence=0.97,
                    bounding_box=BoundingBox(ymin=0.62, xmin=0.15, ymax=0.68, xmax=0.80, label="Net Quantity", estimated_font_height_mm=4.1)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.RETAIL_SALE_PRICE,
                    raw_text="MRP: ₹ 2,999.00 (inclusive of all taxes)",
                    normalized_value="₹ 2,999.00 (inclusive of all taxes)",
                    parsed_attributes={"amount": 2999.0, "taxes_included": True},
                    confidence=0.98,
                    bounding_box=BoundingBox(ymin=0.70, xmin=0.15, ymax=0.76, xmax=0.75, label="MRP", estimated_font_height_mm=4.0)
                ),
                # VIOLATION: Illegal future date 2028
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.DATE_OF_MANUFACTURE,
                    raw_text="Month & Year of Import: 12/2028",
                    normalized_value="12/2028",
                    parsed_attributes={"month": 12, "year": 2028},
                    confidence=0.95,
                    bounding_box=BoundingBox(ymin=0.78, xmin=0.15, ymax=0.83, xmax=0.70, label="Date of Import", estimated_font_height_mm=3.6)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NAME_AND_ADDRESS,
                    raw_text="Imported & Marketed by: Sonic Tech India Ltd, Cyber City, Gurugram, Haryana - 122002",
                    normalized_value="Sonic Tech India Ltd, Cyber City, Gurugram, Haryana - 122002",
                    parsed_attributes={"role": "Importer & Marketer", "pincode": "122002"},
                    confidence=0.96,
                    bounding_box=BoundingBox(ymin=0.85, xmin=0.12, ymax=0.91, xmax=0.88, label="Importer Address", estimated_font_height_mm=3.2)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.CONSUMER_CARE,
                    raw_text="Toll Free: 1800-111-9999 | Email: help@sonictech.in",
                    normalized_value="1800-111-9999, help@sonictech.in",
                    parsed_attributes={"phone": "1800-111-9999", "email": "help@sonictech.in"},
                    confidence=0.96,
                    bounding_box=BoundingBox(ymin=0.92, xmin=0.12, ymax=0.97, xmax=0.88, label="Consumer Care", estimated_font_height_mm=3.0)
                )
                # VIOLATION: Missing COUNTRY_OF_ORIGIN for imported electronics
            ]
        )

    def _get_almond_milk_fixture(self, mm_per_pixel: float) -> ExtractionResult:
        return ExtractionResult(
            product_name="NutriLush Pure Almond Blend",
            brand_name="NutriLush",
            commodity_category="Dairy & Plant Beverages",
            batch_lot_number="NL-AM-108",
            processing_time_ms=595.0,
            source_engine="VLM-Grounding-Engine (Simulated)",
            declarations=[
                # VIOLATION: Missing Generic Name (e.g. "Plant-Based Almond Beverage")
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NET_QUANTITY,
                    raw_text="Net Vol: 1000 ml",
                    normalized_value="1000 ml",
                    parsed_attributes={"amount": 1000.0, "unit": "ml"},
                    confidence=0.97,
                    bounding_box=BoundingBox(ymin=0.60, xmin=0.15, ymax=0.66, xmax=0.50, label="Net Quantity", estimated_font_height_mm=4.5)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.RETAIL_SALE_PRICE,
                    raw_text="MRP ₹ 240.00 (inclusive of all taxes)",
                    normalized_value="₹ 240.00 (inclusive of all taxes)",
                    parsed_attributes={"amount": 240.0, "taxes_included": True},
                    confidence=0.98,
                    bounding_box=BoundingBox(ymin=0.68, xmin=0.15, ymax=0.74, xmax=0.75, label="MRP", estimated_font_height_mm=4.2)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.UNIT_SALE_PRICE,
                    raw_text="USP: ₹ 0.24 / ml",
                    normalized_value="₹ 0.24 / ml",
                    parsed_attributes={"amount": 0.24, "unit": "ml"},
                    confidence=0.97,
                    bounding_box=BoundingBox(ymin=0.75, xmin=0.15, ymax=0.80, xmax=0.55, label="Unit Sale Price", estimated_font_height_mm=4.0)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.DATE_OF_MANUFACTURE,
                    raw_text="Mfg Date: 08/2026",
                    normalized_value="08/2026",
                    parsed_attributes={"month": 8, "year": 2026},
                    confidence=0.98,
                    bounding_box=BoundingBox(ymin=0.81, xmin=0.15, ymax=0.86, xmax=0.50, label="Mfg Date", estimated_font_height_mm=3.8)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.NAME_AND_ADDRESS,
                    raw_text="Manufactured by: NutriLush Foods Pvt Ltd, GIDC Estate, Anand, Gujarat - 388001",
                    normalized_value="NutriLush Foods Pvt Ltd, GIDC Estate, Anand, Gujarat - 388001",
                    parsed_attributes={"role": "Manufacturer", "pincode": "388001"},
                    confidence=0.98,
                    bounding_box=BoundingBox(ymin=0.87, xmin=0.12, ymax=0.92, xmax=0.88, label="Manufacturer Address", estimated_font_height_mm=3.5)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.CONSUMER_CARE,
                    raw_text="Customer Care: 1800-425-0022 | care@nutrilush.in",
                    normalized_value="1800-425-0022, care@nutrilush.in",
                    parsed_attributes={"phone": "1800-425-0022", "email": "care@nutrilush.in"},
                    confidence=0.97,
                    bounding_box=BoundingBox(ymin=0.93, xmin=0.12, ymax=0.97, xmax=0.88, label="Consumer Care", estimated_font_height_mm=3.2)
                ),
                ExtractedDeclarationDTO(
                    id=str(uuid.uuid4()),
                    declaration_type=DeclarationType.COUNTRY_OF_ORIGIN,
                    raw_text="Country of Origin: India",
                    normalized_value="India",
                    parsed_attributes={"country": "India"},
                    confidence=0.99,
                    bounding_box=BoundingBox(ymin=0.81, xmin=0.55, ymax=0.86, xmax=0.88, label="Country of Origin", estimated_font_height_mm=3.8)
                )
            ]
        )
