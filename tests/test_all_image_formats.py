import io
import pytest
from PIL import Image, ImageDraw
import pillow_heif

pillow_heif.register_heif_opener()

def generate_format_image(fmt: str, text: str = "MRP Rs 40.00 (INCL. OF ALL TAXES)\nNET QUANTITY: 250 g") -> bytes:
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 60), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

SUPPORTED_TEST_FORMATS = [
    ("JPEG", "package.jpg", "image/jpeg"),
    ("PNG", "package.png", "image/png"),
    ("WEBP", "package.webp", "image/webp"),
    ("TIFF", "package.tiff", "image/tiff"),
    ("BMP", "package.bmp", "image/bmp"),
    ("GIF", "package.gif", "image/gif"),
    ("HEIF", "package.heic", "image/heic"),
    ("AVIF", "package.avif", "image/avif"),
    ("PPM", "package.ppm", "image/x-portable-pixmap"),
]

@pytest.mark.parametrize("fmt, filename, mime", SUPPORTED_TEST_FORMATS)
def test_universal_image_format_upload(client, fmt, filename, mime):
    """Verify that every standard, modern, and industrial format uploads and registers successfully."""
    img_bytes = generate_format_image(fmt)
    res = client.post(
        "/api/v1/inspections",
        files={"file": (filename, img_bytes, mime)}
    )
    assert res.status_code == 201, f"Failed upload for {fmt}: {res.text}"
    data = res.json()
    assert data["inspection_id"].startswith("insp_")
    assert data["filename"] == filename
    assert data["file_size"] == len(img_bytes)
    assert "image_url" in data
    # Verify image_url is a web-renderable format
    assert data["image_url"].endswith((".jpg", ".png", ".webp"))

@pytest.mark.parametrize("fmt, filename, mime", [
    ("WEBP", "chips.webp", "image/webp"),
    ("HEIF", "chips.heic", "image/heic"),
    ("AVIF", "chips.avif", "image/avif"),
    ("BMP", "chips.bmp", "image/bmp"),
    ("TIFF", "chips.tiff", "image/tiff"),
])
def test_universal_image_format_ocr_and_compliance(client, fmt, filename, mime):
    """Verify that OCR and rule compliance execute end-to-end on diverse image formats."""
    img_bytes = generate_format_image(fmt, "MRP Rs 50.00 (INCL. OF ALL TAXES)\nNET QUANTITY: 100 g")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": (filename, img_bytes, mime)}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 1. Run OCR
    ocr_res = client.post(f"/api/v1/inspections/{inspection_id}/ocr")
    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["total_blocks"] > 0
    assert "MRP" in ocr_data["full_text"]

    # 2. Extract declarations
    ext_res = client.post(f"/api/v1/inspections/{inspection_id}/extract")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert ext_data["fields"]["mrp"]["value"] is not None

    # 3. Evaluate compliance
    eval_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate",
        json={"product_category": "packaged_commodity", "rule_version": "2026.1"}
    )
    assert eval_res.status_code == 200
    comp_data = eval_res.json()
    assert "overall_status" in comp_data
    assert "risk_score" in comp_data

    # 4. Generate PDF report
    rep_res = client.get(f"/api/v1/inspections/{inspection_id}/report")
    assert rep_res.status_code == 200
    assert rep_res.headers["content-type"] == "application/pdf"
    assert len(rep_res.content) > 1000
