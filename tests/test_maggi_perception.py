import pytest
import os
from backend.app.services.ocr.tesseract import TesseractOCRProvider
from backend.app.services.extraction.mock import MockExtractionProvider

MAGGI_IMAGE_PATH = "data/uploads/insp_f6b6ba0feb9b/original.png"

@pytest.mark.asyncio
async def test_maggi_packaging_perception():
    """
    Requirement 11: Test with the provided Maggi image.
    Verifies perception on the actual Maggi package image:
    1. Net Quantity is accurately recognized and normalized to '140 g'.
    2. Manufacturer information identifies Nestlé India.
    3. Product Name identifies MAGGI.
    4. Country of Origin identifies India.
    5. FSSAI / regulatory license is captured in raw OCR.
    6. MRP qualifier without numeric price is marked UNCLEAR (value=null), preventing garbage text.
    """
    assert os.path.exists(MAGGI_IMAGE_PATH), f"Maggi image not found at {MAGGI_IMAGE_PATH}"

    ocr_provider = TesseractOCRProvider()
    ocr_result = await ocr_provider.extract(MAGGI_IMAGE_PATH, inspection_id="test_maggi_perception")

    assert ocr_result.total_blocks > 0
    assert ocr_result.image_width == 554
    assert ocr_result.image_height == 934

    # 1. Verify Quality Analysis
    assert "quality_metrics" in ocr_result.model_dump()
    qm = ocr_result.quality_metrics
    assert qm.get("recommended_upscale", 1.0) >= 2.0

    # 2. Verify Net Quantity OCR presence
    raw_text = ocr_result.full_text.lower()
    assert "140" in raw_text or "140g" in raw_text

    # 3. Verify FSSAI in OCR tokens
    assert any("1001201100168" in b.text or "10021021000783" in b.text for b in ocr_result.blocks)

    # 4. Extract declarations
    ext_provider = MockExtractionProvider()
    declarations = await ext_provider.extract(MAGGI_IMAGE_PATH, ocr_result, inspection_id="test_maggi_perception")

    # Net Quantity: MUST be 140 g
    assert declarations.net_quantity.status == "FOUND"
    assert declarations.net_quantity.value == "140 g"
    assert "140" in declarations.net_quantity.evidence_text
    assert declarations.net_quantity.bounding_box is not None

    # Manufacturer: MUST detect Nestlé
    assert declarations.manufacturer.status == "FOUND"
    assert "Nestl" in declarations.manufacturer.value or "Nestl" in declarations.manufacturer.evidence_text

    # Product Name: MUST detect MAGGI
    assert declarations.product_name.status == "FOUND"
    assert "MAGGI" in declarations.product_name.value.upper()

    # Country of Origin: MUST detect India
    assert declarations.country_of_origin.status == "FOUND"
    assert declarations.country_of_origin.value == "India"

    # MRP: In this packaging image, the price number is obscured/stamped under seal.
    # The system MUST mark it as UNCLEAR with value=null, NEVER outputting garbage like "(incl of all taxes)-"
    assert declarations.mrp.value is None
    assert declarations.mrp.status in ["UNCLEAR", "NOT_FOUND"]
