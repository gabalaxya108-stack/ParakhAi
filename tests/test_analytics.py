import io
import pytest
from PIL import Image

def test_manufacturer_compliance_analytics_api(client):
    # 1. Perform an inspection to guarantee data exists
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(140, 180, 220)).save(buf, format="JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("analytics_sample_pack.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    eval_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate?category=packaged_commodity&rule_version=2026.1"
    )
    assert eval_res.status_code == 200

    # 2. Query GET /api/v1/analytics/manufacturers
    res = client.get("/api/v1/analytics/manufacturers")
    assert res.status_code == 200
    data = res.json()

    assert "total_manufacturers" in data
    assert "total_inspections" in data
    assert "total_potential_violations" in data
    assert "total_repeated_issues" in data
    assert "manufacturers" in data
    assert len(data["manufacturers"]) > 0

    mfr = data["manufacturers"][0]
    assert "manufacturer_name" in mfr
    assert "total_inspections" in mfr
    assert "compliant_inspections" in mfr
    assert "potential_violations" in mfr
    assert "manual_reviews" in mfr
    assert "violation_categories" in mfr
    assert "repeated_issues" in mfr
    assert "status_label" in mfr

    # Crucial statutory language test:
    # Must NOT label a manufacturer "non-compliant" solely from AI screening results!
    assert "non-compliant" not in mfr["status_label"].lower()
    assert ("repeated potential issues detected" in mfr["status_label"].lower() or 
            "no screening issues flagged" in mfr["status_label"].lower() or
            "manual inspection verification advised" in mfr["status_label"].lower())

    # 3. Test filtering by manufacturer substring
    target_mfr = mfr["manufacturer_name"][:5]
    filter_res = client.get(f"/api/v1/analytics/manufacturers?manufacturer={target_mfr}")
    assert filter_res.status_code == 200
    filtered_data = filter_res.json()
    for m in filtered_data["manufacturers"]:
        assert target_mfr.lower() in m["manufacturer_name"].lower()

    # 4. Test filtering by product category
    cat_res = client.get("/api/v1/analytics/manufacturers?product_category=packaged_commodity")
    assert cat_res.status_code == 200

    # 5. Test filtering by non-matching manufacturer
    empty_res = client.get("/api/v1/analytics/manufacturers?manufacturer=NonExistentMfrXYZ999")
    assert empty_res.status_code == 200
    assert len(empty_res.json()["manufacturers"]) == 0
