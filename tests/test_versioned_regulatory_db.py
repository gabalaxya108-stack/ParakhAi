import pytest
from datetime import datetime, timezone
from backend.app.repositories.regulatory_repository import RegulatoryRepository
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.schemas.regulatory import RegulatoryRuleCreate, RegulatoryDocumentCreate
from backend.app.schemas.extraction import ExtractedFieldsContainer, FieldExtractionResult

@pytest.fixture
def repo(tmp_path):
    """Provides a fresh isolated regulatory repository."""
    db_file = str(tmp_path / "test_regulatory.db")
    return RegulatoryRepository(db_path=db_file)

def test_1_rule_lookup(repo):
    """Test 1: Rule lookup by ID returns statutory details and citations."""
    rule = repo.get_rule_by_id("PCR-R6-001")
    assert rule is not None
    assert rule.rule_id == "PCR-R6-001"
    assert rule.field_to_validate == "mrp"
    assert "Rule 6" in rule.section
    assert rule.source_document_id is not None

def test_2_category_applicability(repo):
    """Test 2: Category applicability filters rules appropriately."""
    all_rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01")
    food_rules = repo.get_applicable_rules(category="food", inspection_date="2026-01-01")
    assert len(all_rules) >= 10
    assert len(food_rules) >= 10

def test_3_effective_date_selection(repo):
    """Test 3: Date-based selection retrieves rules that were active on a specific date."""
    # Historical date: 2015-06-01 (before 2017 e-commerce and 2022 USP amendments)
    rules_2015 = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2015-06-01", status="SUPERSEDED")
    rule_ids_2015 = [r.rule_id for r in rules_2015]
    assert "PCR-R6-001" in rule_ids_2015
    assert "PCR-R6-011" not in rule_ids_2015  # USP was not enacted in 2015

    # Modern date: 2026-01-01 (USP is active)
    rules_2026 = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01", status="ACTIVE")
    rule_ids_2026 = [r.rule_id for r in rules_2026]
    assert "PCR-R6-011" in rule_ids_2026

def test_4_amendment_version_selection(repo):
    """Test 4: Amendments catalog tracks statutory version transitions."""
    amendments = repo.list_amendments()
    assert len(amendments) >= 3
    usp_amend = [a for a in amendments if a.rule_id == "PCR-R6-011"]
    assert len(usp_amend) > 0
    assert usp_amend[0].change_type == "SUBSTITUTION"

def test_5_required_declaration_evaluation(repo):
    """Test 5: Required declaration passes when present with high confidence."""
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01")
    mrp_rule = [r for r in rules if r.rule_id == "PCR-R6-001"][0]

    # Present declaration
    check_pass = ComplianceEngine._evaluate_rule(mrp_rule, {"mrp": {"value": "₹40.00", "confidence": 0.95}}, "packaged_commodity")
    assert check_pass.status == "COMPLIANT"

    # Missing declaration
    check_fail = ComplianceEngine._evaluate_rule(mrp_rule, {"mrp": {"value": None, "confidence": 0.0}}, "packaged_commodity")
    assert check_fail.status in ["NEEDS_REVIEW", "MANUAL_REVIEW", "POTENTIAL_VIOLATION"]

def test_6_conditional_rule_evaluation(repo):
    """Test 6: Conditional rule (Unit Sale Price for packages > 100g/ml) is data-driven."""
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01")
    usp_rule = [r for r in rules if r.rule_id == "PCR-R6-011"][0]

    # Package <= 100g -> Exempt
    fields_small = {
        "net_quantity": {"value": "75 g", "confidence": 0.95},
        "mrp": {"value": "₹20", "confidence": 0.95}
    }
    check_exempt = ComplianceEngine._evaluate_rule(usp_rule, fields_small, "packaged_commodity")
    assert check_exempt.status == "COMPLIANT"
    assert "Exempt" in check_exempt.reason

    # Package > 100g -> Mandatory USP
    fields_large = {
        "net_quantity": {"value": "140 g", "confidence": 0.95},
        "mrp": {"value": "₹45", "confidence": 0.95}
    }
    check_large = ComplianceEngine._evaluate_rule(usp_rule, fields_large, "packaged_commodity")
    assert check_large.status == "COMPLIANT"
    assert "Unit Sale Price" in check_large.reason

def test_7_format_validation_driven_by_expression(repo):
    """Test 7: Format check uses validation_expression regex without hardcoded rule IDs."""
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01")
    tax_rule = [r for r in rules if r.rule_id == "PCR-R6-002"][0]

    # Compliant tax-inclusive formulation
    fields_compliant = {
        "mrp": {"value": "₹45 (incl. of all taxes)", "confidence": 0.95, "evidence_text": "MRP ₹45 incl of all taxes"}
    }
    check_pass = ComplianceEngine._evaluate_rule(tax_rule, fields_compliant, "packaged_commodity")
    assert check_pass.status == "COMPLIANT"

    # Non-compliant formulation missing tax mention
    fields_non_compliant = {
        "mrp": {"value": "₹45", "confidence": 0.95, "evidence_text": "MRP ₹45"}
    }
    check_fail = ComplianceEngine._evaluate_rule(tax_rule, fields_non_compliant, "packaged_commodity")
    assert check_fail.status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION", "CONFIRMED_VIOLATION"]

def test_8_rule_supersession(repo):
    """Test 8: Older rule versions are superseded when updated with effective_until."""
    repo.set_rule_status("PCR-R6-001", "SUPERSEDED", effective_until="2025-12-31")
    active_rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01", status="ACTIVE")
    active_ids = [r.rule_id for r in active_rules]
    assert "PCR-R6-001" not in active_ids

def test_9_historical_inspection_reproducibility(repo):
    """Test 9: Historical inspections evaluated at past dates produce identical reproducible results."""
    # Historical date in 2015
    rules_2015 = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2015-05-01", status="SUPERSEDED")
    sample_fields = {
        "mrp": {"value": "₹20", "confidence": 0.95},
        "net_quantity": {"value": "200 g", "confidence": 0.95}
    }
    res_1 = ComplianceEngine.evaluate("insp_hist_01", sample_fields, "packaged_commodity", rules_2015, "2011")
    res_2 = ComplianceEngine.evaluate("insp_hist_01", sample_fields, "packaged_commodity", rules_2015, "2011")

    assert res_1.overall_status == res_2.overall_status
    assert res_1.risk_score == res_2.risk_score
    assert len(res_1.checks) == len(res_2.checks)
    assert res_1.rule_version == "2011"

def test_10_missing_regulatory_rule_handling(repo):
    """Test 10: Non-existent rule ID lookup safely returns None."""
    missing = repo.get_rule_by_id("NON_EXISTENT_RULE_999")
    assert missing is None

def test_11_pending_rule_cannot_be_used(repo):
    """Test 11: Invariant - Rules in PENDING_REVIEW status cannot be used by inspection engine."""
    candidate = RegulatoryRuleCreate(
        rule_id="PCR-CANDIDATE-001",
        rule_version="2026.2",
        title="Candidate Environmental Packaging Rule",
        section="Rule 35",
        requirement="Package must declare recycled plastic percentage.",
        field_to_validate="product_name",
        validation_type="REQUIRED",
        severity="HIGH",
        effective_from="2026-01-01",
        status="PENDING_REVIEW"
    )
    repo.create_rule(candidate)

    # Active lookup must NOT include the pending candidate rule
    active_rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01", status="ACTIVE")
    active_ids = [r.rule_id for r in active_rules]
    assert "PCR-CANDIDATE-001" not in active_ids

def test_12_approved_rule_becomes_active(repo):
    """Test 12: Admin governance transitions rule from PENDING_REVIEW -> APPROVED -> ACTIVE."""
    candidate = RegulatoryRuleCreate(
        rule_id="PCR-GOVERNANCE-001",
        rule_version="2026.2",
        title="Mandatory QR Code Requirement",
        section="Rule 6(1)(h)",
        requirement="Package must provide interactive QR code for statutory declarations.",
        field_to_validate="product_name",
        validation_type="REQUIRED",
        severity="MEDIUM",
        effective_from="2026-01-01",
        status="PENDING_REVIEW"
    )
    repo.create_rule(candidate)

    # Transition to APPROVED
    assert repo.set_rule_status("PCR-GOVERNANCE-001", "APPROVED")
    rule = repo.get_rule_by_id("PCR-GOVERNANCE-001")
    assert rule.status == "APPROVED"

    # Transition to ACTIVE
    assert repo.set_rule_status("PCR-GOVERNANCE-001", "ACTIVE")
    active_rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01", status="ACTIVE")
    active_ids = [r.rule_id for r in active_rules]
    assert "PCR-GOVERNANCE-001" in active_ids

def test_13_rule_source_traceability(repo):
    """Test 13: Every compliance check result preserves official statutory citations."""
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-01-01")
    sample_fields = {
        "mrp": {"value": "₹50 (incl. of all taxes)", "confidence": 0.95},
        "net_quantity": {"value": "100 g", "confidence": 0.95}
    }
    eval_res = ComplianceEngine.evaluate("insp_trace_01", sample_fields, "packaged_commodity", rules, "2026.1")

    for check in eval_res.checks:
        assert check.rule_id is not None
        assert check.requirement is not None
        assert check.section is not None
        assert check.source_document is not None
        assert check.effective_date is not None
