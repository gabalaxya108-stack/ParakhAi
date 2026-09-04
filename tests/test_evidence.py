import io
import pytest
from PIL import Image
from backend.app.schemas.compliance import ComplianceEvaluationResult, RuleCheckResult
from backend.app.schemas.evidence import EvidenceListResponse
from backend.app.services.evidence.service import EvidenceService

def test_evidence_service_absence_never_fabricates_bounding_box():
    comp_result = ComplianceEvaluationResult(
        inspection_id="test_insp_absence",
        overall_status="POTENTIAL_VIOLATION",
        risk_score=35,
        violations=[
            RuleCheckResult(
                rule_id="LM-MRP-001",
                requirement="MRP must be declared",
                field="mrp",
                extracted_value=None,
                detection_status="NOT_FOUND",
                status="POTENTIAL_VIOLATION",
                reason="Mandatory declaration 'mrp' was not found on the package label.",
                severity="CRITICAL",
                confidence=0.0,
                evidence_reference=None
            )
        ],
        checks=[
            RuleCheckResult(
                rule_id="LM-MRP-001",
                requirement="MRP must be declared",
                field="mrp",
                extracted_value=None,
                detection_status="NOT_FOUND",
                status="POTENTIAL_VIOLATION",
                reason="Mandatory declaration 'mrp' was not found on the package label.",
                severity="CRITICAL",
                confidence=0.0,
                evidence_reference=None
            )
        ],
        product_category="packaged_commodity",
        rule_version="2026.1",
        timestamp="2026-09-03T12:00:00Z"
    )

    evidence_res = EvidenceService.build_evidence("test_insp_absence", comp_result)
    assert evidence_res.total == 1
    ev = evidence_res.evidence[0]
    assert ev.rule_id == "LM-MRP-001"
    assert ev.type == "ABSENCE"
    # CRITICAL: Must NEVER fabricate bounding boxes for absent declarations
    assert ev.bounding_box is None
    assert ev.evidence_available is False
    assert ev.detected_text is None
    assert "Evidence of absence" in ev.explanation

def test_evidence_service_incorrect_declaration():
    comp_result = ComplianceEvaluationResult(
        inspection_id="test_insp_incorrect",
        overall_status="POTENTIAL_VIOLATION",
        risk_score=15,
        violations=[],
        checks=[
            RuleCheckResult(
                rule_id="LM-NETQTY-002",
                requirement="Use standard metric symbols (g, kg)",
                field="net_quantity",
                extracted_value="120 gms",
                detection_status="FOUND",
                status="POTENTIAL_VIOLATION",
                reason="Non-standard metric unit symbol detected in '120 gms'.",
                severity="MEDIUM",
                confidence=0.96,
                evidence_reference={
                    "bounding_box": {"x": 100, "y": 600, "width": 150, "height": 40},
                    "source": "ocr"
                }
            )
        ],
        product_category="food",
        rule_version="2026.1",
        timestamp="2026-09-03T12:00:00Z"
    )

    evidence_res = EvidenceService.build_evidence("test_insp_incorrect", comp_result)
    assert evidence_res.total == 1
    ev = evidence_res.evidence[0]
    assert ev.type == "INCORRECT_DECLARATION"
    assert ev.bounding_box is not None
    assert ev.bounding_box.x == 100
    assert ev.bounding_box.width == 150
    assert ev.evidence_available is True
    assert ev.detected_text == "120 gms"
    assert "Evidence of non-compliance" in ev.explanation

def test_evidence_service_uncertain_manual_verification():
    comp_result = ComplianceEvaluationResult(
        inspection_id="test_insp_uncertain",
        overall_status="MANUAL_REVIEW",
        risk_score=15,
        violations=[],
        checks=[
            RuleCheckResult(
                rule_id="LM-DATE-001",
                requirement="Declare month and year of packaging",
                field="packing_date",
                extracted_value="06/??",
                detection_status="UNCLEAR",
                status="MANUAL_REVIEW",
                reason="Declaration detected but confidence (0.42) is below threshold.",
                severity="HIGH",
                confidence=0.42,
                evidence_reference=None  # Region unavailable
            )
        ],
        product_category="packaged_commodity",
        rule_version="2026.1",
        timestamp="2026-09-03T12:00:00Z"
    )

    evidence_res = EvidenceService.build_evidence("test_insp_uncertain", comp_result)
    assert evidence_res.total == 1
    ev = evidence_res.evidence[0]
    assert ev.type == "UNCERTAIN"
    assert ev.bounding_box is None
    assert ev.evidence_available is False
    assert "Evidence unavailable — manual verification required." in ev.explanation

def test_get_inspection_evidence_api(client):
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(180, 200, 220)).save(buf, format="JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("evidence_test.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    # Call GET /api/v1/inspections/{inspection_id}/evidence
    ev_res = client.get(f"/api/v1/inspections/{inspection_id}/evidence")
    assert ev_res.status_code == 200
    data = ev_res.json()
    assert data["inspection_id"] == inspection_id
    assert data["total"] > 0
    assert "summary" in data

    for ev in data["evidence"]:
        assert "evidence_id" in ev
        assert "rule_id" in ev
        assert ev["type"] in ["DETECTED_DECLARATION", "INCORRECT_DECLARATION", "ABSENCE", "UNCERTAIN"]
        assert "explanation" in ev
        assert "confidence" in ev
        assert "evidence_available" in ev

    # Test filtering by type
    filter_res = client.get(f"/api/v1/inspections/{inspection_id}/evidence?type=ABSENCE")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    for ev in filter_data["evidence"]:
        assert ev["type"] == "ABSENCE"
        assert ev["bounding_box"] is None
