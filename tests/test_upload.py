import io
import pytest
from PIL import Image
from backend.app.core.config import settings

def create_test_image(format="JPEG", size=(100, 100), color=(255, 0, 0)) -> bytes:
    """Helper to generate valid in-memory images."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()

def test_valid_upload_jpeg(client):
    img_bytes = create_test_image("JPEG")
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("package_label.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["inspection_id"].startswith("insp_")
    assert data["filename"] == "package_label.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["file_size"] == len(img_bytes)
    assert "image_location" in data
    assert "image_url" in data
    assert data["status"] == "UPLOADED"

def test_valid_upload_png(client):
    img_bytes = create_test_image("PNG")
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("product_nutrition.png", img_bytes, "image/png")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["inspection_id"].startswith("insp_")
    assert data["filename"] == "product_nutrition.png"
    assert data["mime_type"] == "image/png"
    assert data["file_size"] == len(img_bytes)

def test_valid_upload_tiff(client):
    img_bytes = create_test_image("TIFF")
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("high_res_scan.tiff", img_bytes, "image/tiff")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["inspection_id"].startswith("insp_")
    assert data["filename"] == "high_res_scan.tiff"
    assert data["mime_type"] == "image/tiff"
    assert data["file_size"] == len(img_bytes)

def test_invalid_file_type_txt(client):
    fake_doc = b"This is plain text and not a packaging label."
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("notes.txt", fake_doc, "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert "Unsupported file extension" in data["error"]["message"]

def test_invalid_file_signature_spoofed_extension(client):
    fake_image = b"Random payload spoofing a jpeg extension"
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("corrupt.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_FILE_SIGNATURE"

def test_oversized_file(client, monkeypatch):
    # Temporarily set max upload size to 1MB for quick test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    large_payload = b"\xff\xd8\xff" + b"0" * (2 * 1024 * 1024)  # 2MB > 1MB
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("giant_package.jpg", large_payload, "image/jpeg")}
    )
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FILE_TOO_LARGE"
    assert "exceeds maximum limit" in data["error"]["message"]

def test_missing_file(client):
    response = client.post("/api/v1/inspections")
    # Missing required form-data field raises 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REQUEST_VALIDATION_ERROR"

def test_empty_file(client):
    response = client.post(
        "/api/v1/inspections",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "EMPTY_FILE"

def test_get_inspection_by_id(client):
    # Upload an image first
    img_bytes = create_test_image("JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("query_test.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # Retrieve by ID
    get_res = client.get(f"/api/v1/inspections/{inspection_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["inspection_id"] == inspection_id
    assert data["filename"] == "query_test.jpg"

    # Nonexistent ID
    missing_res = client.get("/api/v1/inspections/insp_nonexistent")
    assert missing_res.status_code == 404
