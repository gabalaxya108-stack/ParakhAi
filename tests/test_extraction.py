import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image, ImageDraw

from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox, NormalizedBoundingBox
from backend.app.schemas.extraction import (
    REQUIRED_DECLARATION_FIELDS,
    ExtractedFieldsContainer,
    FieldExtractionResult,
    ExtractionResponse
)
from backend.app.services.extraction.validator import ExtractionValidator
from backend.app.services.extraction.mock import MockExtractionProvider
from backend.app.services.extraction.factory import get_extraction_provider
from backend.app.services.extraction.openai_provider import OpenAIExtractionProvider
from backend.app.core.errors import AppException

def create_test_image(
    size=(800, 1200),
    text: str = "POTATO CHIPS\nMRP Rs 40.00 (INCL. OF ALL TAXES)\nNET QUANTITY: 100 g\nMfd by: Snack Foods Pvt Ltd\nMade in India\nBatch: LOT-2026-X1\nConsumer Care: 1800-111-222"
) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 80), text, fill=(0, 0, 0))
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_correct_extraction_end_to_end(client):
    """Verify POST /inspections/{id}/extract retrieves OCR, extracts fields, and validates schema."""
    # 1. Upload sample package
    img_bytes = create_test_image()
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("chips_bag.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 2. Extract declarations
    extract_res = client.post(f"/api/v1/inspections/{inspection_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()

    assert data["inspection_id"] == inspection_id
    assert "fields" in data
    fields = data["fields"]

    # Check all 11 required fields are present
    for req in REQUIRED_DECLARATION_FIELDS:
        assert req in fields, f"Missing declaration key: {req}"
        field_obj = fields[req]
        assert field_obj["field"] == req
        assert "confidence" in field_obj
        assert "source" in field_obj
        assert "bounding_box" in field_obj
        assert "evidence_text" in field_obj

    # Check MRP field structure matches required specification
    mrp_field = fields["mrp"]
    assert mrp_field["value"] is not None
    assert mrp_field["confidence"] >= 0.50
    assert mrp_field["bounding_box"] is not None
    assert mrp_field["bounding_box"]["width"] > 0
    assert mrp_field["bounding_box"]["height"] > 0
    assert "evidence_text" in mrp_field
    assert mrp_field["evidence_text"] is not None
    assert "MRP" in mrp_field["evidence_text"] or "40" in mrp_field["evidence_text"]

def test_missing_fields_set_to_null():
    """Verify missing fields strictly have value=None, bounding_box=None, and evidence_text=None."""
    provider = MockExtractionProvider()
    ocr = OCRResult(
        inspection_id="test_missing_fields",
        full_text="CRUNCHY MAGIC MASALA",
        blocks=[
            OCRBlock(
                text="CRUNCHY MAGIC MASALA",
                confidence=0.95,
                bounding_box=PixelBoundingBox(x=10, y=10, width=200, height=30),
                page_number=1
            )
        ],
        total_blocks=1,
        image_width=500,
        image_height=500,
        provider="test",
        processing_time_ms=10.0
    )

    import asyncio
    container = asyncio.run(provider.extract("dummy_path", ocr, "test_missing_fields"))

    # Product name is present
    assert container.product_name.value is not None
    assert container.product_name.bounding_box is not None
    assert container.product_name.evidence_text is not None

    # Crucial Invariant: All missing fields MUST be null with null bounding box and null evidence_text
    assert container.mrp.value is None
    assert container.mrp.bounding_box is None
    assert container.mrp.evidence_text is None
    assert container.net_quantity.value is None
    assert container.net_quantity.bounding_box is None
    assert container.net_quantity.evidence_text is None
    assert container.consumer_care.value is None
    assert container.consumer_care.bounding_box is None
    assert container.manufacturer.value is None
    assert container.packer.value is None
    assert container.importer.value is None
    assert container.batch_or_lot_number.value is None

def test_low_confidence_handling():
    """Verify low-confidence OCR text is extracted with accurate confidence reflection."""
    provider = MockExtractionProvider()
    ocr = OCRResult(
        inspection_id="test_low_conf",
        full_text="MRP Rs 40",
        blocks=[
            OCRBlock(
                text="MRP Rs 40",
                confidence=0.45,  # Low confidence
                bounding_box=PixelBoundingBox(x=10, y=10, width=100, height=20),
                page_number=1
            )
        ],
        total_blocks=1,
        image_width=500,
        image_height=500,
        provider="test",
        processing_time_ms=10.0
    )

    import asyncio
    container = asyncio.run(provider.extract("dummy_path", ocr, "test_low_conf"))
    assert container.mrp.value is not None
    assert container.mrp.confidence == 0.45
    assert container.mrp.evidence_text == "MRP Rs 40"

def test_malformed_model_output_rejected():
    """Verify validation rejects outputs with missing field envelopes or invalid types."""
    malformed_payload = {
        "product_name": {"field": "product_name", "value": "Valid Name", "confidence": 0.9},
        "mrp": {"field": "mrp", "value": 40.0}  # Missing confidence, source, bounding_box
    }
    with pytest.raises(Exception):
        ExtractionValidator.validate_model_payload(malformed_payload)

def test_hallucinated_unsupported_fields_rejected():
    """Verify validation rejects outputs with hallucinated or disallowed extra keys."""
    hallucinated_payload = {
        "product_name": {"field": "product_name", "value": "Chips", "confidence": 0.9, "source": "ocr+vision", "bounding_box": None, "evidence_text": None},
        "is_compliant": True,  # Disallowed! Compliance evaluation is NOT the extractor's role
        "hallucinated_field": "fake"
    }
    with pytest.raises(AppException) as exc_info:
        ExtractionValidator.validate_model_payload(hallucinated_payload)
    assert exc_info.value.status_code == 422
    assert "unsupported or hallucinated" in exc_info.value.message or "Invalid" in exc_info.value.message

def test_provider_factory_abstraction(monkeypatch):
    """Verify extraction provider abstraction allows switching via environment variable."""
    # 1. Default / mock
    monkeypatch.setenv("EXTRACTION_PROVIDER", "mock")
    p1 = get_extraction_provider()
    assert isinstance(p1, MockExtractionProvider)

    # 2. Heuristic alias
    monkeypatch.setenv("EXTRACTION_PROVIDER", "heuristic")
    p2 = get_extraction_provider()
    assert isinstance(p2, MockExtractionProvider)

    # 3. OpenAI provider
    monkeypatch.setenv("EXTRACTION_PROVIDER", "openai")
    p3 = get_extraction_provider()
    assert isinstance(p3, OpenAIExtractionProvider)

def test_openai_provider_missing_key_raises_503(monkeypatch):
    """Verify OpenAIExtractionProvider returns 503 when API key is not configured."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    provider = OpenAIExtractionProvider(api_key=None, azure_endpoint=None)
    ocr = OCRResult(
        inspection_id="test_key",
        full_text="",
        blocks=[],
        total_blocks=0,
        image_width=100,
        image_height=100,
        provider="test",
        processing_time_ms=1.0
    )

    import asyncio
    with pytest.raises(AppException) as exc_info:
        asyncio.run(provider.extract("dummy_image.jpg", ocr, "test_key"))
    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "AI_PROVIDER_UNAVAILABLE"

@pytest.mark.asyncio
async def test_openai_provider_successful_mocked_vision_call(monkeypatch, tmp_path):
    """Verify OpenAIExtractionProvider correctly parses and validates multi-modal model output."""
    # Create temporary image
    img_path = str(tmp_path / "test_pkg.jpg")
    Image.new("RGB", (600, 800), color=(200, 200, 200)).save(img_path)

    # Simulated Vision AI structured response
    simulated_model_json = {
        "product_name": {
            "field": "product_name",
            "value": "CRUNCHY POTATO CHIPS",
            "confidence": 0.98,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 80, "width": 400, "height": 60},
            "evidence_text": "CRUNCHY POTATO CHIPS"
        },
        "manufacturer": {
            "field": "manufacturer",
            "value": "Snack Foods Ltd, Industrial Area, Solan HP",
            "confidence": 0.92,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 600, "width": 350, "height": 40},
            "evidence_text": "Mfd by: Snack Foods Ltd, Industrial Area, Solan HP"
        },
        "packer": {
            "field": "packer",
            "value": None,
            "confidence": 0.0,
            "source": "ocr+vision",
            "bounding_box": None,
            "evidence_text": None
        },
        "importer": {
            "field": "importer",
            "value": None,
            "confidence": 0.0,
            "source": "ocr+vision",
            "bounding_box": None,
            "evidence_text": None
        },
        "net_quantity": {
            "field": "net_quantity",
            "value": "100 g",
            "confidence": 0.95,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 200, "width": 150, "height": 40},
            "evidence_text": "NET QUANTITY: 100 g"
        },
        "mrp": {
            "field": "mrp",
            "value": "₹40",
            "confidence": 0.96,
            "source": "ocr+vision",
            "bounding_box": {"x": 420, "y": 310, "width": 160, "height": 50},
            "evidence_text": "MRP ₹40 (INCL. OF ALL TAXES)"
        },
        "packing_date": {
            "field": "packing_date",
            "value": "05/2026",
            "confidence": 0.90,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 400, "width": 120, "height": 30},
            "evidence_text": "PKD: 05/2026"
        },
        "manufacturing_date": {
            "field": "manufacturing_date",
            "value": "04/2026",
            "confidence": 0.90,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 450, "width": 120, "height": 30},
            "evidence_text": "MFD: 04/2026"
        },
        "consumer_care": {
            "field": "consumer_care",
            "value": "care@snackfoods.com, Toll Free 1800-111-222",
            "confidence": 0.94,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 700, "width": 300, "height": 40},
            "evidence_text": "Customer Care: care@snackfoods.com, Toll Free 1800-111-222"
        },
        "country_of_origin": {
            "field": "country_of_origin",
            "value": "India",
            "confidence": 0.99,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 760, "width": 150, "height": 30},
            "evidence_text": "Country of Origin: India"
        },
        "batch_or_lot_number": {
            "field": "batch_or_lot_number",
            "value": "LOT-2026-X1",
            "confidence": 0.93,
            "source": "ocr+vision",
            "bounding_box": {"x": 50, "y": 500, "width": 140, "height": 30},
            "evidence_text": "Batch: LOT-2026-X1"
        }
    }

    import json
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(simulated_model_json)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    provider = OpenAIExtractionProvider(api_key="sk-test-fake-key", model="gpt-4o")
    monkeypatch.setattr(provider, "_get_client", lambda: mock_client)

    ocr = OCRResult(
        inspection_id="test_vision_ai",
        full_text="CRUNCHY POTATO CHIPS MRP ₹40",
        blocks=[],
        total_blocks=0,
        image_width=600,
        image_height=800,
        provider="test",
        processing_time_ms=10.0
    )

    container = await provider.extract(img_path, ocr, "test_vision_ai")

    # Verify extracted fields
    assert container.mrp.value == "₹40"
    assert container.mrp.confidence == 0.96
    assert container.mrp.source == "ocr+vision"
    assert container.mrp.evidence_text == "MRP ₹40 (INCL. OF ALL TAXES)"
    assert container.mrp.bounding_box.x == 420
    assert container.mrp.bounding_box.y == 310
    assert container.mrp.bounding_box.width == 160
    assert container.mrp.bounding_box.height == 50

    # Verify null for missing declarations
    assert container.packer.value is None
    assert container.packer.bounding_box is None
    assert container.importer.value is None

def test_get_cached_extraction(client):
    """Verify GET /inspections/{id}/extract retrieves cached extraction results."""
    img_bytes = create_test_image()
    upload_res = client.post("/api/v1/inspections", files={"file": ("chips_cached.jpg", img_bytes, "image/jpeg")})
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # Initial extract
    extract_res = client.post(f"/api/v1/inspections/{inspection_id}/extract")
    assert extract_res.status_code == 200

    # Retrieve cached via GET /extract
    cached_res = client.get(f"/api/v1/inspections/{inspection_id}/extract")
    assert cached_res.status_code == 200
    assert cached_res.json()["inspection_id"] == inspection_id

def test_extract_nonexistent_inspection(client):
    """Verify 404 is returned when requesting extraction for nonexistent inspection ID."""
    res = client.post("/api/v1/inspections/nonexistent_insp_id_999/extract")
    assert res.status_code == 404
