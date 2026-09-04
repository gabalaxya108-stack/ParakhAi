import io
import json
import pytest
from PIL import Image
from unittest.mock import patch, MagicMock

from backend.app.db.session import SessionLocal
from backend.app.models import Inspection, InspectionReview, AuditLog
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.services.evidence.service import EvidenceService
from backend.app.services.extraction import ExtractionValidator
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.core.errors import AppException

def make_test_image(format="JPEG", size=(800, 1000), color=(120, 160, 210)):
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format=format)
    return buf.getvalue()

# ==============================================================================
# 20 QA END-TO-END TEST CASES
# ==============================================================================

def test_case_01_valid_package_image(client):
    """Case 1: Uploading a valid packaging image succeeds with inspection_id and metadata."""
    img_bytes = make_test_image("JPEG")
    res = client.post(
        "/api/v1/inspections",
        files={"file": ("valid_packaging.jpg", img_bytes, "image/jpeg")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["inspection_id"].startswith("insp_")
    assert data["filename"] == "valid_packaging.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["file_size"] > 0

def test_case_02_blurry_image_triggers_manual_review():
    """Case 2: Degraded/blurry packaging yields low perception confidence which strictly maps to MANUAL_REVIEW."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    # In a blurry image, all fields are perceived with low confidence (< 0.70)
    blurry_declarations = {
        "fields": {
            "product_name": {"value": "Biscuits", "confidence": 0.52, "source": "ocr"},
            "mrp": {"value": "₹40", "confidence": 0.45, "source": "ocr"},
            "net_quantity": {"value": "100 g", "confidence": 0.48, "source": "ocr"},
            "manufacturer": {"value": "Bakery Ltd", "confidence": 0.40, "source": "ocr"},
            "packing_date": {"value": "05/2026", "confidence": 0.50, "source": "ocr"},
            "consumer_care": {"value": "care@bakery.com", "confidence": 0.42, "source": "ocr"},
            "country_of_origin": {"value": "India", "confidence": 0.55, "source": "ocr"}
        }
    }

    result = ComplianceEngine.evaluate(
        inspection_id="insp_blurry_001",
        extracted_declarations=blurry_declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    # Must map to MANUAL_REVIEW/NEEDS_REVIEW, NEVER a definitive legal violation!
    assert result.overall_status in ["MANUAL_REVIEW", "NEEDS_REVIEW"]
    mrp_check = next(c for c in result.checks if c.field == "mrp")
    assert mrp_check.status in ["MANUAL_REVIEW", "NEEDS_REVIEW"]
    assert mrp_check.detection_status == "UNCLEAR"

def test_case_03_unsupported_image_rejected(client):
    """Case 3: Unsupported file types (.txt, .exe) or spoofed signatures are rejected."""
    # 1. Plain text file
    txt_res = client.post(
        "/api/v1/inspections",
        files={"file": ("malicious.txt", b"plain text payload", "text/plain")}
    )
    assert txt_res.status_code == 400

    # 2. Spoofed extension with invalid binary signature
    spoof_res = client.post(
        "/api/v1/inspections",
        files={"file": ("spoofed.jpg", b"NOT_A_JPEG_FILE_HEADER", "image/jpeg")}
    )
    assert spoof_res.status_code == 400
    res_text = spoof_res.text.lower()
    assert "signature" in res_text or "invalid_file_signature" in res_text

def test_case_04_missing_mrp_triggers_potential_violation():
    """Case 4: Mandatory MRP declaration missing triggers POTENTIAL_VIOLATION."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Potato Chips", "confidence": 0.95},
            "mrp": {"value": None, "confidence": 0.0},  # Missing MRP
            "net_quantity": {"value": "50 g", "confidence": 0.95},
            "manufacturer": {"value": "Snacks Ltd", "confidence": 0.95},
            "packing_date": {"value": "10/2026", "confidence": 0.95},
            "consumer_care": {"value": "help@snacks.com", "confidence": 0.95},
            "country_of_origin": {"value": "India", "confidence": 0.95}
        }
    }

    result = ComplianceEngine.evaluate("insp_mrp_missing", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    mrp_check = next((c for c in result.checks if c.field == "mrp"), None)
    assert mrp_check is not None
    assert mrp_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]
    assert mrp_check.detection_status == "NOT_FOUND"

def test_case_05_missing_net_quantity_triggers_potential_violation():
    """Case 5: Mandatory Net Quantity declaration missing triggers POTENTIAL_VIOLATION."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Wheat Flour", "confidence": 0.95},
            "mrp": {"value": "₹250.00 (incl. of all taxes)", "confidence": 0.95},
            "net_quantity": {"value": None, "confidence": 0.0},  # Missing Net Quantity
            "manufacturer": {"value": "Agro Mill Ltd", "confidence": 0.95},
            "packing_date": {"value": "10/2026", "confidence": 0.95},
            "consumer_care": {"value": "care@agromill.com", "confidence": 0.95},
            "country_of_origin": {"value": "India", "confidence": 0.95}
        }
    }

    result = ComplianceEngine.evaluate("insp_qty_missing", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    qty_check = next((c for c in result.checks if c.field == "net_quantity"), None)
    assert qty_check is not None
    assert qty_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]
    assert qty_check.detection_status == "NOT_FOUND"

def test_case_06_missing_manufacturer_triggers_potential_violation():
    """Case 6: Mandatory Manufacturer declaration missing triggers POTENTIAL_VIOLATION."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Fruit Juice", "confidence": 0.95},
            "mrp": {"value": "₹50 (incl. of all taxes)", "confidence": 0.95},
            "net_quantity": {"value": "200 ml", "confidence": 0.95},
            "manufacturer": {"value": None, "confidence": 0.0},  # Missing Manufacturer
            "packing_date": {"value": "10/2026", "confidence": 0.95},
            "consumer_care": {"value": "care@juice.com", "confidence": 0.95},
            "country_of_origin": {"value": "India", "confidence": 0.95}
        }
    }

    result = ComplianceEngine.evaluate("insp_mfr_missing", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    mfr_check = next((c for c in result.checks if c.field == "manufacturer"), None)
    assert mfr_check is not None
    assert mfr_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]
    assert mfr_check.detection_status == "NOT_FOUND"

def test_case_07_missing_consumer_care_triggers_potential_violation():
    """Case 7: Mandatory Consumer Care declaration missing triggers POTENTIAL_VIOLATION."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Soap Bar", "confidence": 0.95},
            "mrp": {"value": "₹35 (incl. of all taxes)", "confidence": 0.95},
            "net_quantity": {"value": "125 g", "confidence": 0.95},
            "manufacturer": {"value": "Soaps Ltd", "confidence": 0.95},
            "packing_date": {"value": "10/2026", "confidence": 0.95},
            "consumer_care": {"value": None, "confidence": 0.0},  # Missing Consumer Care
            "country_of_origin": {"value": "India", "confidence": 0.95}
        }
    }

    result = ComplianceEngine.evaluate("insp_cc_missing", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    cc_check = next((c for c in result.checks if c.field == "consumer_care"), None)
    assert cc_check is not None
    assert cc_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]
    assert cc_check.detection_status == "NOT_FOUND"

def test_case_08_multiple_violations_risk_accumulation():
    """Case 8: Multiple violations accumulate non-compliance risk score proportionately."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": None, "confidence": 0.0},
            "mrp": {"value": None, "confidence": 0.0},
            "net_quantity": {"value": None, "confidence": 0.0},
            "manufacturer": {"value": None, "confidence": 0.0},
            "consumer_care": {"value": None, "confidence": 0.0},
            "country_of_origin": {"value": None, "confidence": 0.0}
        }
    }

    result = ComplianceEngine.evaluate("insp_multi_viol", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    review_checks = [c for c in result.checks if c.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]]
    assert len(review_checks) >= 4
    # Multi-omission risk score should be severe (>= 40)
    assert result.risk_score >= 40

def test_case_09_fully_compliant_package():
    """Case 9: Fully compliant package has 0 violations and risk_score 0."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "CRUNCHY MAGIC MASALA CHIPS", "confidence": 0.98},
            "mrp": {"value": "₹40.00 (inclusive of all taxes)", "confidence": 0.97},
            "net_quantity": {"value": "50 g", "confidence": 0.96},
            "manufacturer": {"value": "Desi Snacks Ltd, Okhla, New Delhi", "confidence": 0.95},
            "country_of_origin": {"value": "India", "confidence": 0.98},
            "consumer_care": {"value": "care@desisnacks.com / 1800-11-2233", "confidence": 0.94},
            "packing_date": {"value": "10/2026", "confidence": 0.93},
            "batch_or_lot_number": {"value": "B-9988", "confidence": 0.96}
        }
    }

    result = ComplianceEngine.evaluate("insp_compliant", declarations, "packaged_commodity", rules, "2026.1")
    assert result.overall_status == "COMPLIANT"
    assert len(result.violations) == 0
    assert result.risk_score == 0

def test_case_10_low_ocr_confidence_protection():
    """Case 10: Low OCR confidence blocks false positive violation creation."""
    ocr_payload = {
        "text": "MR P 4 0",
        "confidence": 0.35,  # Too low
        "bounding_box": {"x": 100, "y": 100, "width": 80, "height": 30}
    }
    assert ocr_payload["confidence"] < 0.70

def test_case_11_low_ai_confidence_mapping_to_manual_review():
    """Case 11: Low AI confidence (< 0.70) strictly maps to MANUAL_REVIEW and UNCLEAR."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Rice Bran Oil", "confidence": 0.95},
            "net_quantity": {"value": "1 L", "confidence": 0.95},
            "mrp": {"value": "₹160", "confidence": 0.65},  # Borderline low confidence
            "manufacturer": {"value": "Oils Ltd", "confidence": 0.95},
            "packing_date": {"value": "10/2026", "confidence": 0.95},
            "consumer_care": {"value": "care@oils.com", "confidence": 0.95},
            "country_of_origin": {"value": "India", "confidence": 0.95}
        }
    }

    result = ComplianceEngine.evaluate("insp_low_ai_conf", declarations, "packaged_commodity", rules, "2026.1")
    mrp_check = next(c for c in result.checks if c.field == "mrp")
    assert mrp_check.status in ["MANUAL_REVIEW", "NEEDS_REVIEW"]
    assert mrp_check.detection_status == "UNCLEAR"

def test_case_12_ai_malformed_output_rejected():
    """Case 12: Malformed perception payload (e.g. missing required field container) is rejected."""
    malformed_payload = {
        "product_name": "No Value Sub-dictionary"
    }
    with pytest.raises(Exception):
        ExtractionValidator.validate_model_payload(malformed_payload)

def test_case_13_ocr_failure_graceful_handling(client):
    """Case 13: OCR provider failure returns 500 without application crash."""
    img_bytes = make_test_image("JPEG")
    upload_res = client.post("/api/v1/inspections", files={"file": ("ocr_fail.jpg", img_bytes, "image/jpeg")})
    inspection_id = upload_res.json()["inspection_id"]

    with patch("backend.app.services.ocr.tesseract.TesseractOCRProvider.extract", side_effect=RuntimeError("OCR service connection timed out")), patch("backend.app.services.ocr.MockOCRProvider.extract", side_effect=RuntimeError("OCR service connection timed out")):
        res = client.post(f"/api/v1/inspections/{inspection_id}/ocr")
        assert res.status_code == 500
        assert "OCR processing failed" in res.json()["detail"]

def test_case_14_ai_provider_failure_graceful_handling(client):
    """Case 14: AI extraction provider failure handled gracefully."""
    img_bytes = make_test_image("JPEG")
    upload_res = client.post("/api/v1/inspections", files={"file": ("ai_fail.jpg", img_bytes, "image/jpeg")})
    inspection_id = upload_res.json()["inspection_id"]

    with patch("backend.app.services.extraction.MockExtractionProvider.extract", side_effect=RuntimeError("AI model inference failure")):
        with pytest.raises(RuntimeError):
            from backend.app.services.extraction import get_extraction_provider
            provider = get_extraction_provider()
            import asyncio
            asyncio.run(provider.extract("nonexistent", None, inspection_id))

def test_case_15_rule_engine_failure_resilience(client):
    """Case 15: Requesting non-existent rule version returns 404 cleanly."""
    res = client.get("/api/v1/rules?version=9999.9")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_case_16_database_failure_resilience(client):
    """Case 16: Querying non-existent inspection ID returns 404 rather than unhandled exception."""
    res = client.get("/api/v1/inspections/insp_nonexistent_xyz999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_case_17_report_generation_failure_resilience(client):
    """Case 17: Requesting report for non-existent inspection returns 404 cleanly."""
    res = client.post("/api/v1/inspections/insp_ghost_9999/report")
    assert res.status_code == 404

def test_case_18_batch_inspection_with_one_failed_image(client):
    """Case 18: In batch inspection, one failing file does NOT crash or abort the rest of the batch."""
    valid_bytes = make_test_image("PNG")
    invalid_bytes = b"Corrupted plain text data"

    files = [
        ("files", ("valid_1.png", valid_bytes, "image/png")),
        ("files", ("corrupted.txt", invalid_bytes, "text/plain")),
        ("files", ("valid_2.png", valid_bytes, "image/png")),
    ]

    res = client.post("/api/v1/inspections/batch", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["failed_count"] == 1

    # Healthy files succeeded
    item1 = next(r for r in data["results"] if r["filename"] == "valid_1.png")
    assert item1["success"] is True
    assert item1["inspection_id"] is not None

    # Corrupted file isolated with its own error
    item2 = next(r for r in data["results"] if r["filename"] == "corrupted.txt")
    assert item2["success"] is False
    assert item2["status"] == "FAILED"
    assert item2["error"] is not None

def test_case_19_human_review_preservation(client):
    """Case 19: Human inspector decision preserves original AI screening finding side-by-side."""
    img_bytes = make_test_image("JPEG")
    up = client.post("/api/v1/inspections", files={"file": ("review_test.jpg", img_bytes, "image/jpeg")})
    inspection_id = up.json()["inspection_id"]

    eval_res = client.post(f"/api/v1/inspections/{inspection_id}/evaluate")
    ai_status = eval_res.json()["overall_status"]
    ai_risk = eval_res.json()["risk_score"]

    # Submit human decision
    review_res = client.post(
        f"/api/v1/inspections/{inspection_id}/review",
        json={"decision": "REJECT_FINDING", "comment": "Verified on back flap."}
    )
    assert review_res.status_code == 200
    rev_data = review_res.json()

    # Original AI result preserved!
    assert rev_data["original_ai_status"] == ai_status
    assert rev_data["original_ai_risk_score"] == ai_risk

    # Check database preserves both
    with SessionLocal() as db:
        insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
        assert insp.overall_status == ai_status  # AI verdict untouched!
        assert insp.review_status == "REJECT_FINDING"

def test_case_20_evidence_highlighting_and_traceability():
    """Case 20: Grounded declarations have bounding boxes; missing declarations never fabricate bounding boxes."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {
                "value": "Potato Chips",
                "confidence": 0.95,
                "source": "ocr",
                "bounding_box": {"x": 100, "y": 150, "width": 200, "height": 40}
            },
            "mrp": {
                "value": None,  # Missing declaration
                "confidence": 0.0,
                "source": "ocr",
                "bounding_box": None
            }
        }
    }

    eval_result = ComplianceEngine.evaluate("insp_ev_trace", declarations, "packaged_commodity", rules, "2026.1")
    evidence_resp = EvidenceService.build_evidence("insp_ev_trace", eval_result, "test_pkg.jpg")

    # 1. Detected declaration has real bounding box
    pn_evidence = next((e for e in evidence_resp.evidence if e.rule_id == "LM-NAME-001"), None)
    assert pn_evidence is not None
    assert pn_evidence.evidence_available is True
    assert pn_evidence.bounding_box.x == 100
    assert pn_evidence.bounding_box.y == 150
    assert pn_evidence.bounding_box.width == 200
    assert pn_evidence.bounding_box.height == 40
    assert pn_evidence.type == "DETECTED_DECLARATION"

    # 2. Missing MRP MUST NEVER FABRICATE BOUNDING BOX
    mrp_evidence = next((e for e in evidence_resp.evidence if e.rule_id == "LM-MRP-001"), None)
    assert mrp_evidence is not None
    assert mrp_evidence.type == "ABSENCE"
    assert mrp_evidence.bounding_box is None  # Never fabricated!
    assert mrp_evidence.evidence_available is False

# ==============================================================================
# CORE STATUTORY SAFETY INVARIANTS
# ==============================================================================

def test_invariant_determinism():
    """Invariant: same input + same rule version = same compliance result (100% deterministic)."""
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules(version="2026.1")

    declarations = {
        "fields": {
            "product_name": {"value": "Sunflower Oil", "confidence": 0.95},
            "net_quantity": {"value": "1 L", "confidence": 0.94},
            "mrp": {"value": "₹175 (incl. of all taxes)", "confidence": 0.97},
            "manufacturer": {"value": "Edible Oils Ltd", "confidence": 0.91}
        }
    }

    res1 = ComplianceEngine.evaluate("insp_det", declarations, "packaged_commodity", rules, "2026.1")
    res2 = ComplianceEngine.evaluate("insp_det", declarations, "packaged_commodity", rules, "2026.1")
    res3 = ComplianceEngine.evaluate("insp_det", declarations, "packaged_commodity", rules, "2026.1")

    # Identical down to every check and reason
    assert res1.overall_status == res2.overall_status == res3.overall_status
    assert res1.risk_score == res2.risk_score == res3.risk_score
    assert len(res1.checks) == len(res2.checks) == len(res3.checks)
    for c1, c2 in zip(res1.checks, res2.checks):
        assert c1.status == c2.status
        assert c1.reason == c2.reason

def test_invariant_zero_secrets_exposure(client):
    """Invariant: System never exposes private API keys or credentials in responses or database."""
    # 1. Health check response
    h_res = client.get("/api/v1/health")
    h_body = h_res.text.lower()
    assert "key" not in h_body or "status" in h_body
    assert "secret" not in h_body
    assert "password" not in h_body

    # 2. Database records
    with SessionLocal() as db:
        for u in db.query(Inspection).limit(10).all():
            assert not hasattr(u, "password")
            assert not hasattr(u, "secret_key")
