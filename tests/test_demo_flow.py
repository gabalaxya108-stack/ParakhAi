import requests
import io
from PIL import Image, ImageDraw

def generate_sample_indian_package():
    # Generate realistic packaging image with text
    img = Image.new("RGB", (900, 1200), color=(18, 24, 38))
    draw = ImageDraw.Draw(img)

    # Background cards
    draw.rectangle([40, 40, 860, 1160], outline=(40, 60, 95), width=3)
    draw.rectangle([60, 60, 840, 200], fill=(220, 38, 38)) # Red header band

    # Brand Title
    draw.text((80, 80), "DESI MAGIC MASALA CHIPS", fill=(255, 255, 255))
    draw.text((80, 140), "Authentic Spiced Potato Crisps", fill=(255, 230, 230))

    # Declarations Panel
    draw.rectangle([80, 250, 820, 1100], fill=(28, 36, 52), outline=(50, 75, 110), width=2)
    draw.text((100, 280), "STATUTORY DECLARATIONS / CONSUMER INFO", fill=(140, 180, 240))

    # Fields
    y = 350
    lines = [
        ("COMMON / GENERIC NAME:", "Potato Chips / Ready-to-eat Savouries"),
        ("NET QUANTITY:", "50 g"),
        ("MAXIMUM RETAIL PRICE (MRP):", "Rs 40.00 (inclusive of all taxes)"),
        ("UNIT SALE PRICE:", "Rs 0.80 per g"),
        ("MONTH & YEAR OF PACKAGING:", "08/2026"),
        ("BATCH / LOT NUMBER:", "LOT-2026-MM-492"),
        ("COUNTRY OF ORIGIN:", "India"),
        ("MANUFACTURED & PACKED BY:", "Desi Snacks & Foods Pvt. Ltd."),
        ("REGISTERED ADDRESS:", "Plot 42, Food Park, Okhla Phase III, New Delhi 110020"),
        ("CONSUMER CARE HELPLINE:", "1800-11-9988 / care@desisnacks.gov.in")
    ]

    for label, val in lines:
        draw.text((100, y), f"{label} {val}", fill=(255, 255, 255))
        y += 70

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def test_full_demo_flow_step_by_step(client):
    # Step 1: Open Dashboard (metrics check)
    dash_res = client.get("/api/v1/inspections/meta/dashboard")
    assert dash_res.status_code == 200
    initial_metrics = dash_res.json()
    initial_total = initial_metrics["total_inspections"]

    # Step 2 & 3: Scan Product & Upload Real Indian Package Image
    pkg_bytes = generate_sample_indian_package()
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("desi_magic_masala.jpg", pkg_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    insp_data = upload_res.json()
    inspection_id = insp_data["inspection_id"]

    # Step 4 & 5: OCR + Vision AI Extract Declarations
    ocr_res = client.post(f"/api/v1/inspections/{inspection_id}/ocr")
    assert ocr_res.status_code == 200

    extract_res = client.post(f"/api/v1/inspections/{inspection_id}/extract")
    assert extract_res.status_code == 200
    decl_data = extract_res.json()
    assert "fields" in decl_data
    assert decl_data["fields"]["mrp"]["value"] is not None
    assert decl_data["fields"]["net_quantity"]["value"] is not None

    # Step 6: Verify Structured Declarations with Confidence
    for field_name in ["mrp", "net_quantity", "manufacturer", "consumer_care"]:
        f_obj = decl_data["fields"][field_name]
        assert f_obj["confidence"] >= 0.0

    # Step 7 & 8: Rule Engine Evaluates Applicable Requirements -> Inspection Result
    rule_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate",
        json={"product_category": "packaged_commodity", "rule_version": "2026.1"}
    )
    assert rule_res.status_code == 200
    comp_data = rule_res.json()
    assert "overall_status" in comp_data
    assert "risk_score" in comp_data
    assert len(comp_data["checks"]) > 0

    # Step 9, 10 & 11: Inspector Examines Violations and Evidence Grounding
    for check in comp_data["checks"]:
        assert "rule_id" in check
        assert "requirement" in check
        assert "confidence" in check
        if check["evidence_reference"]:
            ev = check["evidence_reference"]
            assert "bounding_box" in ev

    # Step 12: Inspector Reviews the Finding (Human-in-the-loop)
    review_res = client.post(
        f"/api/v1/inspections/{inspection_id}/reviews",
        json={
            "decision": "CONFIRM_FINDING",
            "comment": "Pre-demo physical verification completed by inspector",
            "reviewer": "inspector_demo_lead"
        }
    )
    assert review_res.status_code == 201
    rev_data = review_res.json()
    assert rev_data["decision"] == "CONFIRM_FINDING"

    # Step 13: System Generates PDF Inspection Report
    report_res = client.get(f"/api/v1/inspections/{inspection_id}/report")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert len(report_res.content) > 1000

    # Step 14: Inspection Appears in History
    history_res = client.get("/api/v1/inspections")
    assert history_res.status_code == 200
    history = history_res.json()
    assert any(item["inspection_id"] == inspection_id for item in history)

    # Step 15: Dashboard Analytics Update
    updated_dash_res = client.get("/api/v1/inspections/meta/dashboard")
    assert updated_dash_res.status_code == 200
    updated_metrics = updated_dash_res.json()
    assert updated_metrics["total_inspections"] >= initial_total + 1
