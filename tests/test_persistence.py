import io
import pytest
from PIL import Image
from backend.app.db.session import SessionLocal
from backend.app.models import (
    User, Product, RuleVersion, Rule,
    Inspection, Image as ImageModel, OCRResult, Declaration,
    ComplianceCheck, Violation, Evidence,
    InspectionReview, AuditLog
)
from backend.app.services.database_persistence import DatabasePersistenceService

def test_postgresql_all_entities_table_creation():
    with SessionLocal() as db:
        # Verify queries against all 13 entities succeed
        assert db.query(User).count() >= 0
        assert db.query(Product).count() >= 0
        assert db.query(RuleVersion).count() >= 0
        assert db.query(Rule).count() >= 0
        assert db.query(Inspection).count() >= 0
        assert db.query(ImageModel).count() >= 0
        assert db.query(OCRResult).count() >= 0
        assert db.query(Declaration).count() >= 0
        assert db.query(ComplianceCheck).count() >= 0
        assert db.query(Violation).count() >= 0
        assert db.query(Evidence).count() >= 0
        assert db.query(InspectionReview).count() >= 0
        assert db.query(AuditLog).count() >= 0

def test_end_to_end_postgresql_persistence_and_retrieval(client):
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(120, 140, 200)).save(buf, format="JPEG")

    # 1. Upload
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("postgres_test_pack.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # 2. Evaluate Compliance (which also triggers OCR & Extraction in PostgreSQL)
    eval_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate?category=packaged_commodity&rule_version=2026.1"
    )
    assert eval_res.status_code == 200

    # 3. Verify complete preservation in PostgreSQL via GET /inspections/{id}
    detail_res = client.get(f"/api/v1/inspections/{inspection_id}")
    assert detail_res.status_code == 200
    dossier = detail_res.json()

    # Verify all preserved attributes specified by user
    assert dossier["inspection_id"] == inspection_id
    assert "created_at" in dossier  # timestamp
    assert "inspector" in dossier  # inspector
    assert dossier["inspector"]["username"] == "inspector_lm"
    assert "product" in dossier  # product
    assert "model_provider_version" in dossier  # model/provider version
    assert "rule_version" in dossier  # rule version
    assert dossier["rule_version"] == "2026.1"
    assert "extracted_declarations" in dossier  # extracted declarations
    assert "compliance_result" in dossier  # compliance result
    assert "evidence" in dossier  # evidence
    assert "review_status" in dossier  # review status
    assert dossier["review_status"] in ["PENDING", "APPROVED", "REJECTED", "ACTION_REQUIRED"]

    # 4. Verify GET /api/v1/inspections returns historical list from PostgreSQL
    list_res = client.get("/api/v1/inspections")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) > 0
    match = next((i for i in items if i["inspection_id"] == inspection_id), None)
    assert match is not None
    assert "product" in match
    assert "risk_score" in match
    assert "review_status" in match

    # 5. Security check: Verify NO secrets are stored in database
    with SessionLocal() as db:
        insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
        assert insp is not None
        # Verify no passwords or secret api keys are on user or inspection records
        user = db.query(User).filter(User.id == insp.user_id).first()
        assert not hasattr(user, "password")
        assert not hasattr(user, "api_key")
        assert not hasattr(user, "secret")
        assert not hasattr(insp, "api_key")
        assert not hasattr(insp, "secret")
