import io
import pytest
from PIL import Image
from backend.app.db.session import SessionLocal
from backend.app.models import Inspection, InspectionReview, AuditLog

def test_human_in_the_loop_review_flow(client):
    # 1. Ingest product package
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(140, 160, 200)).save(buf, format="JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("review_test_package.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 2. Run AI evaluation
    eval_res = client.post(f"/api/v1/inspections/{inspection_id}/evaluate?category=packaged_commodity&rule_version=2026.1")
    assert eval_res.status_code == 200
    ai_status = eval_res.json()["overall_status"]
    ai_risk = eval_res.json()["risk_score"]

    # 3. Submit human review: CONFIRM_FINDING
    review_res = client.post(
        f"/api/v1/inspections/{inspection_id}/review",
        json={
            "decision": "CONFIRM_FINDING",
            "comment": "Physical label confirms missing mandatory consumer care contacts.",
            "reviewer": "inspector_patil"
        }
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["inspection_id"] == inspection_id
    assert data["decision"] == "CONFIRM_FINDING"
    assert data["decision_label"] == "Confirmed Finding"
    assert "consumer care" in data["comment"].lower()
    assert data["original_ai_status"] == ai_status
    assert data["original_ai_risk_score"] == ai_risk

    # 4. Critical Invariant Check: Verify original AI result was NOT overwritten
    with SessionLocal() as db:
        insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
        assert insp is not None
        assert insp.overall_status == ai_status  # AI result unchanged!
        assert insp.risk_score == ai_risk        # Risk score unchanged!
        assert insp.review_status == "CONFIRM_FINDING"

        # Verify AuditLog created
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.inspection_id == insp.id, AuditLog.action == "INSPECTION_REVIEW_SUBMITTED")
            .first()
        )
        assert audit is not None
        assert audit.change_details_json["decision"] == "CONFIRM_FINDING"
        assert audit.change_details_json["preserved_original_ai_status"] == ai_status

    # 5. Retrieve reviews history via GET
    hist_res = client.get(f"/api/v1/inspections/{inspection_id}/reviews")
    assert hist_res.status_code == 200
    reviews_list = hist_res.json()
    assert len(reviews_list) >= 1
    latest = reviews_list[0]
    assert latest["decision"] == "CONFIRM_FINDING"
    assert latest["original_ai_status"] == ai_status

    # 6. Test alternative decision: REQUEST_MANUAL_VERIFICATION
    review_res_2 = client.post(
        f"/api/v1/inspections/{inspection_id}/review",
        json={
            "decision": "REQUEST_MANUAL_VERIFICATION",
            "comment": "Font size is near borderline threshold; scheduled for lab measurement."
        }
    )
    assert review_res_2.status_code == 200
    assert review_res_2.json()["decision"] == "REQUEST_MANUAL_VERIFICATION"
