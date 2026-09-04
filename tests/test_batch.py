import io
import pytest
from PIL import Image

def test_batch_inspection_success_and_resilience(client):
    # Prepare 2 valid images
    buf1 = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(100, 150, 200)).save(buf1, format="JPEG")
    
    buf2 = io.BytesIO()
    Image.new("RGB", (600, 800), color=(120, 180, 140)).save(buf2, format="PNG")

    # Prepare 1 invalid file (.txt file that fails image validation)
    invalid_txt = b"This is a text file, not a valid packaging photograph."

    files = [
        ("files", ("batch_item_1.jpg", buf1.getvalue(), "image/jpeg")),
        ("files", ("batch_item_2.png", buf2.getvalue(), "image/png")),
        ("files", ("invalid_note.txt", invalid_txt, "text/plain")),
    ]

    # Call POST /api/v1/inspections/batch
    res = client.post("/api/v1/inspections/batch?category=food&rule_version=2026.1", files=files)
    assert res.status_code == 200
    data = res.json()

    assert "batch_id" in data
    assert data["total"] == 3
    assert "compliant_count" in data
    assert "potential_violations_count" in data
    assert "manual_review_count" in data
    assert "high_risk_count" in data
    assert data["failed_count"] == 1  # The invalid .txt file failed

    results = data["results"]
    assert len(results) == 3

    # Check item 1 (JPEG) succeeded
    item1 = next((r for r in results if r["filename"] == "batch_item_1.jpg"), None)
    assert item1 is not None
    assert item1["success"] is True
    assert item1["inspection_id"] is not None
    assert item1["status"] in ["COMPLIANT", "CONFIRMED_VIOLATION", "NON_COMPLIANT", "NEEDS_REVIEW", "POTENTIAL_VIOLATION", "MANUAL_REVIEW"]
    assert "average_confidence" in item1

    # Check item 2 (PNG) succeeded
    item2 = next((r for r in results if r["filename"] == "batch_item_2.png"), None)
    assert item2 is not None
    assert item2["success"] is True
    assert item2["inspection_id"] is not None

    # Check item 3 (TXT) failed gracefully without failing the entire batch
    item3 = next((r for r in results if r["filename"] == "invalid_note.txt"), None)
    assert item3 is not None
    assert item3["success"] is False
    assert item3["status"] == "FAILED"
    assert item3["error"] is not None
    assert "format" in item3["error"].lower() or "type" in item3["error"].lower()
