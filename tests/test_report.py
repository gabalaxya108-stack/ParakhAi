import io
import pytest
from PIL import Image

def test_generate_pdf_report_api(client):
    # 1. Upload product
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(140, 170, 220)).save(buf, format="JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("report_test_pack.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 2. Evaluate compliance
    eval_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate?category=food&rule_version=2026.1"
    )
    assert eval_res.status_code == 200

    # 3. Call POST /api/v1/inspections/{inspection_id}/report
    report_res = client.post(f"/api/v1/inspections/{inspection_id}/report")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert f"Inspection_Report_{inspection_id}.pdf" in report_res.headers["content-disposition"]

    pdf_bytes = report_res.content
    assert len(pdf_bytes) > 1000
    # Standard PDF magic header
    assert pdf_bytes.startswith(b"%PDF-")

    # 4. Also verify GET route works for direct browser download
    get_report_res = client.get(f"/api/v1/inspections/{inspection_id}/report")
    assert get_report_res.status_code == 200
    assert get_report_res.content.startswith(b"%PDF-")
