import io
import pytest
from PIL import Image, ImageDraw
from backend.app.services.ocr.factory import get_ocr_provider
from backend.app.services.ocr.mock import MockOCRProvider
from backend.app.services.ocr.tesseract import TesseractOCRProvider

def create_test_image(size=(800, 1000), text: str = "MRP Rs 40.00 (INCL. OF ALL TAXES)\nNET QUANTITY: 100 g") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw high-contrast text for OCR
    draw.text((50, 80), text, fill=(0, 0, 0))
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_ocr_provider_factory_default():
    provider = get_ocr_provider("mock")
    assert isinstance(provider, MockOCRProvider)

    # Tesseract provider
    tess_provider = get_ocr_provider("tesseract")
    assert isinstance(tess_provider, TesseractOCRProvider)

    # Unknown provider should fall back to mock
    fallback = get_ocr_provider("unknown_vendor")
    assert isinstance(fallback, MockOCRProvider)

@pytest.mark.asyncio
async def test_mock_ocr_provider_direct_extraction():
    provider = MockOCRProvider()
    img_bytes = create_test_image(size=(800, 1000))
    result = await provider.extract(img_bytes, inspection_id="test_direct_123")

    assert result.inspection_id == "test_direct_123"
    assert result.image_width == 800
    assert result.image_height == 1000
    assert result.total_blocks > 0
    assert len(result.blocks) == result.total_blocks
    assert result.provider == "mock"
    assert result.processing_time_ms >= 0

    # Verify blocks preserve all required fields
    for block in result.blocks:
        assert isinstance(block.text, str) and len(block.text) > 0
        assert 0.0 <= block.confidence <= 1.0
        assert block.page_number == 1
        assert block.bounding_box.x >= 0
        assert block.bounding_box.y >= 0
        assert block.bounding_box.width > 0
        assert block.bounding_box.height > 0
        if block.normalized_box:
            assert 0.0 <= block.normalized_box.ymin <= 1.0
            assert 0.0 <= block.normalized_box.xmin <= 1.0
            assert 0.0 <= block.normalized_box.ymax <= 1.0
            assert 0.0 <= block.normalized_box.xmax <= 1.0

def test_post_inspection_ocr_endpoint_success(client):
    # 1. Upload an image with legible text
    img_bytes = create_test_image(
        size=(800, 1200),
        text="MRP Rs 40.00 (INCL. OF ALL TAXES)\nNET QUANTITY: 200 g\nManufactured by: Test Foods Pvt Ltd"
    )
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("chips_package.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 2. Call POST /api/v1/inspections/{inspection_id}/ocr
    ocr_res = client.post(f"/api/v1/inspections/{inspection_id}/ocr")
    assert ocr_res.status_code == 200
    data = ocr_res.json()

    assert data["inspection_id"] == inspection_id
    assert data["provider"] in ("tesseract", "mock")
    assert data["image_width"] == 800
    assert data["image_height"] == 1200
    assert data["total_blocks"] > 0
    assert len(data["full_text"]) > 0

    # Check for expected block structure
    found_mrp = False
    for block in data["blocks"]:
        assert "text" in block
        assert "confidence" in block
        assert "bounding_box" in block
        assert "x" in block["bounding_box"]
        assert "y" in block["bounding_box"]
        assert "width" in block["bounding_box"]
        assert "height" in block["bounding_box"]
        assert block["page_number"] == 1

        if "MRP" in block["text"]:
            found_mrp = True
            assert block["confidence"] >= 0.50
            assert block["bounding_box"]["width"] > 0
            assert block["bounding_box"]["height"] > 0

    assert found_mrp, "Expected MRP text block to be detected in OCR"

    # 3. Verify cached GET /api/v1/inspections/{inspection_id}/ocr
    cached_res = client.get(f"/api/v1/inspections/{inspection_id}/ocr")
    assert cached_res.status_code == 200
    cached_data = cached_res.json()
    assert cached_data["inspection_id"] == inspection_id
    assert cached_data["total_blocks"] == data["total_blocks"]

def test_ocr_nonexistent_inspection(client):
    response = client.post("/api/v1/inspections/insp_does_not_exist/ocr")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_get_ocr_before_processing(client):
    # Upload an image but do not run OCR yet
    img_bytes = create_test_image()
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("unprocessed.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # Try GET before POST
    get_res = client.get(f"/api/v1/inspections/{inspection_id}/ocr")
    assert get_res.status_code == 404
    assert "No OCR extraction has been performed" in get_res.json()["detail"]
