import io
import os
import pytest
from PIL import Image, ImageDraw
from backend.app.services.ocr.tesseract import TesseractOCRProvider
from backend.app.services.ocr.preprocessor import ImagePreprocessingPipeline
from backend.app.core.errors import AppException

def generate_synthetic_package_image(
    lines: list = None,
    size: tuple = (1000, 600),
    bg_color: tuple = (255, 255, 255)
) -> bytes:
    """Creates an in-memory package image with high-contrast text declarations."""
    if lines is None:
        lines = [
            "MRP Rs 40.00 (INCL. OF ALL TAXES)",
            "NET QUANTITY: 200 g",
            "Mfd by: Tasty Snacks Pvt Ltd, New Delhi 110001",
            "Consumer Care Helpline: 1800-222-333",
            "Batch No: TS-2026-X1"
        ]

    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)

    y = 50
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 70

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.mark.asyncio
async def test_01_tesseract_availability():
    """Verify local Tesseract executable detection and version."""
    provider = TesseractOCRProvider()
    assert provider.executable_path is not None, "Tesseract executable path must be resolved"
    assert os.path.exists(provider.executable_path), f"Executable must exist at {provider.executable_path}"

    version = provider.get_version()
    assert version.startswith("5."), f"Expected Tesseract v5.x, got '{version}'"

    languages = provider.get_installed_languages()
    assert "eng" in languages, "English language pack 'eng' must be available"

@pytest.mark.asyncio
async def test_02_english_ocr():
    """Verify English text recognition on a packaged commodity label."""
    provider = TesseractOCRProvider()
    img_bytes = generate_synthetic_package_image([
        "MRP Rs 50.00 (INCLUSIVE OF ALL TAXES)",
        "NET WEIGHT: 500 g",
        "COUNTRY OF ORIGIN: INDIA"
    ])

    res = await provider.extract(img_bytes, inspection_id="test_eng_01", lang="eng")
    assert res.total_blocks > 0
    assert "MRP" in res.full_text
    assert "50.00" in res.full_text
    assert "INDIA" in res.full_text

@pytest.mark.asyncio
async def test_03_hindi_ocr():
    """Verify multilingual language configuration supports Devanagari/Hindi."""
    provider = TesseractOCRProvider()
    installed = provider.get_installed_languages()
    if "hin" not in installed:
        pytest.skip("Hindi language pack 'hin' not installed in test environment")

    resolved_lang = provider.resolve_languages("eng+hin")
    assert "hin" in resolved_lang

    # Test extracting bilingual package if available
    maggi_path = "data/uploads/insp_f6b6ba0feb9b/original.png"
    if os.path.exists(maggi_path):
        res = await provider.extract(maggi_path, inspection_id="test_hin_01", lang="eng+hin")
        assert res.total_blocks > 0
        assert len(res.full_text) > 0

@pytest.mark.asyncio
async def test_04_bounding_boxes():
    """Verify bounding box coordinates are positive and within image bounds."""
    provider = TesseractOCRProvider()
    img_bytes = generate_synthetic_package_image(size=(800, 500))

    res = await provider.extract(img_bytes, inspection_id="test_boxes_01")
    assert res.image_width == 800
    assert res.image_height == 500

    for block in res.blocks:
        box = block.bounding_box
        assert box.x >= 0, "X coordinate must be non-negative"
        assert box.y >= 0, "Y coordinate must be non-negative"
        assert box.width > 0, "Width must be positive"
        assert box.height > 0, "Height must be positive"
        assert box.x + box.width <= res.image_width + 5, "Box cannot exceed image width"
        assert box.y + box.height <= res.image_height + 5, "Box cannot exceed image height"

        if block.normalized_box:
            norm = block.normalized_box
            assert 0.0 <= norm.ymin <= 1.0
            assert 0.0 <= norm.xmin <= 1.0
            assert 0.0 <= norm.ymax <= 1.0
            assert 0.0 <= norm.xmax <= 1.0
            assert norm.ymax >= norm.ymin
            assert norm.xmax >= norm.xmin

@pytest.mark.asyncio
async def test_05_confidence_extraction():
    """Verify confidence metrics are scaled correctly between 0.0 and 1.0."""
    provider = TesseractOCRProvider()
    img_bytes = generate_synthetic_package_image()

    res = await provider.extract(img_bytes, inspection_id="test_conf_01")
    assert len(res.blocks) > 0

    for block in res.blocks:
        assert 0.0 <= block.confidence <= 1.0, f"Confidence {block.confidence} out of range [0, 1]"

    # Verify high-contrast text yields high confidence (> 60%)
    high_conf_blocks = [b for b in res.blocks if b.confidence >= 0.60]
    assert len(high_conf_blocks) > 0, "Expected clear text to produce high-confidence detections"

@pytest.mark.asyncio
async def test_06_invalid_image():
    """Verify corrupt or unreadable image bytes raise a clean AppException."""
    provider = TesseractOCRProvider()
    corrupted_bytes = b"NOT_A_VALID_IMAGE_FILE_HEADER_12345"

    with pytest.raises(AppException) as exc_info:
        await provider.extract(corrupted_bytes, inspection_id="test_invalid")

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "INVALID_IMAGE"

@pytest.mark.asyncio
async def test_07_missing_tesseract_binary():
    """Verify that an invalid tesseract path triggers a 503 TESSERACT_NOT_FOUND error."""
    provider = TesseractOCRProvider(tesseract_cmd="/invalid/path/to/nonexistent_tesseract")
    img_bytes = generate_synthetic_package_image()

    with pytest.raises(AppException) as exc_info:
        await provider.extract(img_bytes, inspection_id="test_missing_cmd")

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "TESSERACT_NOT_FOUND"

def test_08_missing_language_fallback():
    """Verify that an uninstalled language code falls back gracefully without crashing."""
    provider = TesseractOCRProvider()
    resolved = provider.resolve_languages("nonexistent_language_xyz+another_fake_lang")
    assert "eng" in resolved or resolved in provider.get_installed_languages()

@pytest.mark.asyncio
async def test_09_empty_ocr_result_blank_image():
    """Verify that a solid blank image produces a clean 0-block result without crashing."""
    provider = TesseractOCRProvider()
    blank_img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    buf = io.BytesIO()
    blank_img.save(buf, format="PNG")

    res = await provider.extract(buf.getvalue(), inspection_id="test_blank")
    assert res.total_blocks == 0
    assert res.full_text == ""
    assert res.blocks == []
    assert res.results == []

def test_10_multi_pass_preprocessing():
    """Verify that ImagePreprocessingPipeline generates original, enhanced, binarized, adaptive, and morph variants."""
    img_bytes = generate_synthetic_package_image()
    variants = ImagePreprocessingPipeline.generate_variants(img_bytes)

    assert "original" in variants
    assert "enhanced" in variants
    assert "binarized" in variants
    assert "adaptive" in variants
    assert "morph" in variants

    for name, v in variants.items():
        assert "image" in v
        assert "scale_factor" in v
        assert v["scale_factor"] >= 1.0
        assert "original_dims" in v
        assert len(v["original_dims"]) == 2

def test_11_system_diagnostic_endpoint(client):
    """Verify GET /api/v1/system/ocr returns Tesseract installation diagnostic payload."""
    res = client.get("/api/v1/system/ocr")
    assert res.status_code == 200
    data = res.json()

    assert data["provider"] == "tesseract"
    assert data["available"] is True
    assert data["version"].startswith("5.")
    assert isinstance(data["languages"], list)
    assert len(data["languages"]) > 0
    assert "eng" in data["configured_languages"]

@pytest.mark.asyncio
async def test_12_coordinate_backprojection_mapping():
    """Verify that coordinates on upscaled variants correctly map back to the original image space."""
    provider = TesseractOCRProvider()
    # Create small image (400x300) which triggers upscaling
    small_img_bytes = generate_synthetic_package_image(
        lines=["MRP Rs 10.00", "NET QTY: 50 g"],
        size=(400, 300)
    )

    res = await provider.extract(small_img_bytes, inspection_id="test_scale_map")
    assert res.image_width == 400
    assert res.image_height == 300

    for block in res.blocks:
        # All bounding box coordinates must lie inside the 400x300 original dimension
        assert 0 <= block.bounding_box.x < 400
        assert 0 <= block.bounding_box.y < 300
        assert block.bounding_box.x + block.bounding_box.width <= 400 + 2
        assert block.bounding_box.y + block.bounding_box.height <= 300 + 2
