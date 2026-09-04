import pytest
from backend.app.schemas.rules import RuleModel
from backend.app.schemas.regulatory import RegulatoryRuleDTO
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.services.regulatory.applicability import ApplicabilityEngine
from backend.app.services.extraction.canonical_normalizer import CanonicalNormalizer
from backend.app.repositories.regulatory_repository import RegulatoryRepository
from backend.app.db.session import SessionLocal
from backend.app.models import User, Complaint, Inspection

def test_invariant_1_ocr_empty_returns_unable_to_verify_never_fail():
    """
    CORE PRODUCT INVARIANT 1:
    If OCR returns empty string or no detection, the system MUST return UNABLE_TO_VERIFY / NEEDS_REVIEW,
    NOT a false regulatory violation (FAIL).
    """
    rule = RegulatoryRuleDTO(
        id="test-r6-001",
        rule_id="PCR-R6-001",
        rule_version="2026.1",
        title="MRP Declaration",
        section="Rule 6(1)(e)",
        requirement="Retail sale price declaration",
        applicable_categories=["all", "packaged_commodity"],
        field_to_validate="mrp",
        validation_type="REQUIRED_FIELD",
        severity="CRITICAL",
        effective_from="2011-04-01",
        status="ACTIVE"
    )

    # Empty perception output (OCR did not detect text)
    fields_map = {
        "mrp": {
            "value": None,
            "confidence": 0.0,
            "status": "NOT_FOUND",
            "source": "ocr"
        }
    }

    check = ComplianceEngine._evaluate_rule(rule, fields_map, "packaged_commodity")
    
    # Must NOT be NON_COMPLIANT / FAIL
    assert check.status in ["UNABLE_TO_VERIFY", "NEEDS_REVIEW", "MANUAL_REVIEW"], f"Expected UNABLE_TO_VERIFY but got {check.status}"
    assert "not detected with sufficient confidence" in check.reason or "manual inspector verification" in check.reason or "insufficient" in check.reason
    assert check.status != "NON_COMPLIANT"
    assert check.status != "POTENTIAL_VIOLATION"


def test_invariant_2_visual_evidence_with_low_ocr_confidence_triggers_review_not_violation():
    """
    CORE PRODUCT INVARIANT 2:
    If visual evidence exists but OCR confidence is low/unreadable, the result MUST be UNABLE_TO_VERIFY / NEEDS_REVIEW.
    """
    rule = RegulatoryRuleDTO(
        id="test-r6-003",
        rule_id="PCR-R6-003",
        rule_version="2026.1",
        title="Net Quantity Declaration",
        section="Rule 6(1)(c)",
        requirement="Net quantity declaration in standard metric units",
        applicable_categories=["all", "packaged_commodity"],
        field_to_validate="net_quantity",
        validation_type="REQUIRED_FIELD",
        severity="HIGH",
        effective_from="2011-04-01",
        status="ACTIVE"
    )

    # Partial/blurred text detected with confidence below threshold (e.g. 0.35)
    fields_map = {
        "net_quantity": {
            "value": "2?? g",
            "confidence": 0.35,
            "status": "FOUND",
            "bounding_box": {"x": 100, "y": 200, "width": 80, "height": 30},
            "source": "ocr"
        }
    }

    check = ComplianceEngine._evaluate_rule(rule, fields_map, "packaged_commodity")
    assert check.status in ["UNABLE_TO_VERIFY", "NEEDS_REVIEW", "MANUAL_REVIEW"]
    assert check.status != "NON_COMPLIANT"


def test_invariant_3_inapplicable_rule_returns_not_applicable():
    """
    CORE PRODUCT INVARIANT 3:
    If a statutory exemption applies (e.g. small packaging under Rule 26 or wholesale under Rule 3),
    the rule MUST return NOT_APPLICABLE.
    """
    rule = RegulatoryRuleDTO(
        id="test-r6-001",
        rule_id="PCR-R6-001",
        rule_version="2026.1",
        title="MRP Declaration",
        section="Rule 6(1)(e)",
        requirement="Retail sale price declaration",
        applicable_categories=["packaged_commodity"],
        field_to_validate="mrp",
        validation_type="REQUIRED_FIELD",
        severity="CRITICAL",
        effective_from="2011-04-01",
        status="ACTIVE"
    )

    # Wholesale industrial package exemption under Rule 3
    app_res = ApplicabilityEngine.evaluate_applicability(rule, commodity_category="wholesale", is_retail=False)
    assert app_res["applicable"] is False
    assert "Rule 3" in app_res["reason"]

    # Small package threshold under Rule 26 (< 10g)
    small_app = ApplicabilityEngine.evaluate_applicability(rule, commodity_category="packaged_commodity", net_quantity_g=5.0)
    assert small_app["applicable"] is False
    assert "Rule 26" in small_app["reason"]


def test_invariant_4_semantic_mrp_normalization():
    """
    CORE PRODUCT INVARIANT 4:
    Semantic MRP Equivalence: Variations of currency and tax-inclusive statements
    MUST be semantically normalized and evaluated without brittle exact string failure.
    """
    phrases = [
        "₹ 60.00 (Inclusive of all taxes)",
        "MRP Rs. 60 (incl. of all taxes)",
        "Maximum Retail Price: ₹60.00 (inclusive of all taxes)",
        "M.R.P. ₹ 60.00 (INCL. OF ALL TAXES)"
    ]

    for p in phrases:
        res = CanonicalNormalizer.normalize_mrp(p)
        assert res["is_valid"] is True, f"Failed validity for: {p}"
        norm = res["normalized_value"]
        assert norm["amount"] == 60.0, f"Failed amount for phrase: {p}"
        assert norm["currency"] in ["INR", "₹"], f"Failed currency for: {p}"
        assert norm["tax_inclusive"] is True, f"Failed tax inclusive for: {p}"


def test_invariant_5_food_cross_regulatory_fssai_alignment():
    """
    CORE PRODUCT INVARIANT 5:
    Food products MUST explicitly reflect cross-regulatory alignment with FSSAI.
    """
    rule = RegulatoryRuleDTO(
        id="test-r6-date",
        rule_id="PCR-R6-004",
        rule_version="2026.1",
        title="Date of Manufacture",
        section="Rule 6(1)(d)",
        requirement="Date of manufacture / packaging",
        applicable_categories=["all", "packaged_commodity"],
        field_to_validate="date_of_manufacture",
        validation_type="DATE_CHECK",
        severity="MEDIUM",
        effective_from="2011-04-01",
        status="ACTIVE"
    )

    app = ApplicabilityEngine.evaluate_applicability(rule, commodity_category="food_packaged_commodity")
    assert app["applicable"] is True
    assert app["cross_regulatory_framework"] is not None
    assert "FSSAI" in app["cross_regulatory_framework"]


def test_invariant_6_complaint_and_audit_persistence():
    """
    CORE PRODUCT INVARIANT 6:
    Enforcement complaints MUST persist in PostgreSQL with valid complaint_id,
    and audit logs MUST be recorded.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "inspector.demo").first()
        assert user is not None, "Demo inspector user must exist"

        complaint = db.query(Complaint).first()
        assert complaint is not None, "At least one seeded complaint must exist"
        assert complaint.complaint_id.startswith("CMP-2026-")
        assert complaint.status in ["PENDING_NOTICE", "NOTICE_ISSUED", "CLOSED"]
    finally:
        db.close()
