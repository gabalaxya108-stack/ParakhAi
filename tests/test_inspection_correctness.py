import pytest
from backend.app.schemas.ocr import OCRResult, OCRBlock, PixelBoundingBox
from backend.app.schemas.extraction import (
    ExtractedFieldsContainer,
    FieldExtractionResult
)
from backend.app.schemas.regulatory import RegulatoryRuleDTO
from backend.app.services.extraction.quality_filter import DeclarationQualityFilter
from backend.app.services.extraction.reconciliation import ExtractionReconciler
from backend.app.services.compliance.engine import ComplianceEngine


def make_field_result(field: str, val: str = None, status: str = "NOT_FOUND", conf: float = 0.0, raw: str = None, source: str = "qwen_vision") -> FieldExtractionResult:
    return FieldExtractionResult(
        field=field,
        value=val,
        confidence=conf,
        source=source,
        bounding_box=PixelBoundingBox(x=10, y=10, width=100, height=20) if val else None,
        evidence_text=raw or val,
        status=status,
        raw_value=raw or val,
        conflict_detected=False,
        candidates=[]
    )


def make_container(**kwargs) -> ExtractedFieldsContainer:
    defaults = {
        "product_name": make_field_result("product_name"),
        "manufacturer": make_field_result("manufacturer"),
        "packer": make_field_result("packer"),
        "importer": make_field_result("importer"),
        "net_quantity": make_field_result("net_quantity"),
        "mrp": make_field_result("mrp"),
        "packing_date": make_field_result("packing_date"),
        "manufacturing_date": make_field_result("manufacturing_date"),
        "consumer_care": make_field_result("consumer_care"),
        "country_of_origin": make_field_result("country_of_origin"),
        "batch_or_lot_number": make_field_result("batch_or_lot_number")
    }
    defaults.update(kwargs)
    return ExtractedFieldsContainer(**defaults)


# Test 1: Product name + MRP label near each other
def test_1_product_name_quality_filter_rejects_mrp_header():
    mrp_block = OCRBlock(
        text="MAXIMUM RETAIL PRICE (MRP)",
        confidence=0.92,
        bounding_box=PixelBoundingBox(x=50, y=20, width=300, height=30)
    )
    status, val, conf, raw = DeclarationQualityFilter.filter_product_name(mrp_block)
    assert status == "UNCLEAR"
    assert val is None


# Test 2: Tesseract and Qwen agree on product name
def test_2_tesseract_qwen_agree_corroborates():
    t_fields = make_container(product_name=make_field_result("product_name", "Moong Dal Namkeen", "FOUND", 0.90))
    q_fields = make_container(product_name=make_field_result("product_name", "Moong Dal Namkeen", "FOUND", 0.95))

    reconciled, ledger = ExtractionReconciler.reconcile(t_fields, q_fields)
    assert reconciled.product_name.status == "FOUND"
    assert reconciled.product_name.confidence == 0.99
    assert reconciled.product_name.conflict_detected is False


# Test 3: Tesseract and Qwen disagree on MRP value
def test_3_tesseract_qwen_disagree_on_same_field_triggers_conflict():
    t_fields = make_container(mrp=make_field_result("mrp", "₹ 50.00", "FOUND", 0.88))
    q_fields = make_container(mrp=make_field_result("mrp", "₹ 60.00", "FOUND", 0.92))

    reconciled, ledger = ExtractionReconciler.reconcile(t_fields, q_fields)
    assert reconciled.mrp.conflict_detected is True
    assert reconciled.mrp.status == "UNCLEAR"
    assert reconciled.mrp.confidence <= 0.50


# Test 4: Tesseract and Qwen identify different fields (No False Conflict)
def test_4_tesseract_mrp_header_and_qwen_product_name_no_false_conflict():
    t_fields = make_container(product_name=make_field_result("product_name", "MAXIMUM RETAIL PRICE (MRP)", "FOUND", 0.90))
    q_fields = make_container(product_name=make_field_result("product_name", "Moong Dal Namkeen", "FOUND", 0.95))

    reconciled, ledger = ExtractionReconciler.reconcile(t_fields, q_fields)
    assert reconciled.product_name.value == "Moong Dal Namkeen"
    assert reconciled.product_name.status == "FOUND"
    assert reconciled.product_name.conflict_detected is False


# Test 5 & 6 & 7: Date-based rule applicability (Only current active rule evaluated)
def test_5_6_7_only_active_applicable_rule_evaluated():
    from backend.app.repositories.regulatory_repository import RegulatoryRepository
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-09-01T00:00:00Z")

    rule_ids = [r.rule_id for r in rules]
    assert "PCR-R6-001" in rule_ids
    for r in rules:
        assert r.status == "ACTIVE"


# Test 8: Manufacturing Date vs Packing Date (Rule 6(1)(d) satisfied by Mfg Date)
def test_8_mfg_date_satisfies_rule_6_1_d():
    container = make_container(
        manufacturing_date=make_field_result("manufacturing_date", "01/05/2024", "FOUND", 0.95),
        packing_date=make_field_result("packing_date", None, "NOT_FOUND", 0.0)
    )

    rule = RegulatoryRuleDTO(
        id="rule_8",
        rule_id="PCR-R6-006",
        rule_version="2026.1",
        title="Month and Year of Manufacture or Packing",
        requirement="Month and Year of Manufacture or Packing",
        section="Rule 6",
        sub_rule="6(1)(d)",
        validation_type="REQUIRED",
        field_to_validate="packing_date",
        applicable_categories=["all"],
        effective_from="2011-03-01T00:00:00Z",
        status="ACTIVE",
        severity="HIGH"
    )

    res = ComplianceEngine._evaluate_statutory_date(rule, container.model_dump())
    assert res.status == "COMPLIANT"
    assert "01/05/2024" in res.reason


# Test 9: Missing declaration returns POTENTIAL_VIOLATION
def test_9_missing_declaration_returns_potential_violation():
    container = make_container(net_quantity=make_field_result("net_quantity", None, "NOT_FOUND", 0.0))

    rule = RegulatoryRuleDTO(
        id="rule_9",
        rule_id="PCR-R6-003",
        rule_version="2026.1",
        title="Mandatory Net Quantity Declaration",
        requirement="Mandatory Net Quantity Declaration",
        section="Rule 6",
        sub_rule="6(1)(c)",
        validation_type="REQUIRED",
        field_to_validate="net_quantity",
        applicable_categories=["all"],
        effective_from="2011-03-01T00:00:00Z",
        status="ACTIVE",
        severity="CRITICAL"
    )

    res = ComplianceEngine._evaluate_rule(rule, container.model_dump(), "packaged_commodity")
    assert res.status in ["NEEDS_REVIEW", "POTENTIAL_VIOLATION"]
    assert res.detection_status == "NOT_FOUND"


# Test 10: Unreadable declaration returns MANUAL_REVIEW (NEEDS_REVIEW)
def test_10_unreadable_declaration_returns_manual_review():
    container = make_container(mrp=make_field_result("mrp", None, "UNCLEAR", 0.40, raw="MRP ₹"))

    rule = RegulatoryRuleDTO(
        id="rule_10",
        rule_id="PCR-R6-001",
        rule_version="2026.1",
        title="Mandatory MRP Declaration",
        requirement="Mandatory MRP Declaration",
        section="Rule 6",
        sub_rule="6(1)(e)",
        validation_type="REQUIRED",
        field_to_validate="mrp",
        applicable_categories=["all"],
        effective_from="2011-03-01T00:00:00Z",
        status="ACTIVE",
        severity="CRITICAL"
    )

    res = ComplianceEngine._evaluate_rule(rule, container.model_dump(), "packaged_commodity")
    assert res.status in ["NEEDS_REVIEW", "MANUAL_REVIEW"]
    assert res.detection_status == "UNCLEAR"


# Test 11: Compliant package test (0 false violations)
def test_11_compliant_package_evaluates_cleanly():
    container = make_container(
        product_name=make_field_result("product_name", "Moong Dal Namkeen", "FOUND", 0.95),
        manufacturer=make_field_result("manufacturer", "XYZ Foods Pvt Ltd", "FOUND", 0.95),
        net_quantity=make_field_result("net_quantity", "200 g", "FOUND", 0.95),
        mrp=make_field_result("mrp", "₹ 60.00 (Inclusive of all taxes)", "FOUND", 0.95, raw="₹ 60.00 (Inclusive of all taxes)"),
        manufacturing_date=make_field_result("manufacturing_date", "01/05/2024", "FOUND", 0.95),
        consumer_care=make_field_result("consumer_care", "care@xyzfoods.com 1800-123-4567", "FOUND", 0.95),
        country_of_origin=make_field_result("country_of_origin", "INDIA", "FOUND", 0.95),
        batch_or_lot_number=make_field_result("batch_or_lot_number", "A1234", "FOUND", 0.95)
    )

    from backend.app.repositories.regulatory_repository import RegulatoryRepository
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules("packaged_commodity")

    eval_res = ComplianceEngine.evaluate("test_compliant", container, "packaged_commodity", rules, "2026.1")
    assert eval_res.overall_status == "COMPLIANT"
    assert len(eval_res.violations) == 0
    assert eval_res.risk_score == 0


# Test 12: Non-compliant package still receives genuine findings
def test_12_non_compliant_package_triggers_genuine_violations():
    container = make_container(
        product_name=make_field_result("product_name", "Moong Dal Namkeen", "FOUND", 0.95),
        mrp=make_field_result("mrp", None, "NOT_FOUND", 0.0), # Missing MRP!
        net_quantity=make_field_result("net_quantity", "200 gms", "FOUND", 0.95) # Non-standard unit 'gms'!
    )

    from backend.app.repositories.regulatory_repository import RegulatoryRepository
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules("packaged_commodity")

    eval_res = ComplianceEngine.evaluate("test_defective", container, "packaged_commodity", rules, "2026.1")
    assert eval_res.overall_status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION"]
    assert len(eval_res.violations) >= 1
    assert eval_res.risk_score > 0
