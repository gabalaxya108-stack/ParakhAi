import pytest
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.services.compliance.canonical_requirements import CanonicalAggregator
from backend.app.services.extraction.canonical_normalizer import CanonicalNormalizer
from backend.app.repositories.regulatory_repository import RegulatoryRepository

def test_canonical_normalizer_mrp_semantic_equivalence():
    """Verify semantic normalization of various MRP tax-inclusive formulations."""
    variants = [
        "MAXIMUM RETAIL PRICE ₹60.00 (Inclusive of all taxes)",
        "MRP Rs. 60/- incl. of all taxes",
        "MRP 60.00 inclusive of taxes",
        "Rs 60 incl of all taxes"
    ]
    for v in variants:
        res = CanonicalNormalizer.normalize_mrp(v)
        assert res["normalized_value"]["amount"] == 60.0
        assert res["normalized_value"]["tax_inclusive"] is True
        assert res["is_valid"] is True

def test_canonical_normalizer_net_quantity_canonical_units():
    """Verify conversion of various units to canonical metric symbols."""
    res1 = CanonicalNormalizer.normalize_net_quantity("Net Qty: 140 g")
    assert res1["normalized_value"]["magnitude"] == 140.0
    assert res1["normalized_value"]["canonical_unit"] == "g"
    assert res1["normalized_value"]["is_standard_metric_symbol"] is True

    res2 = CanonicalNormalizer.normalize_net_quantity("140 gm")
    assert res2["normalized_value"]["canonical_unit"] == "g"
    assert res2["normalized_value"]["is_standard_metric_symbol"] is False # 'gm' is non-standard per Rule 11

def test_canonical_requirements_zero_duplicate_mrp():
    """Verify that multiple granular MRP rules are unified into exactly 1 canonical MRP requirement."""
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-09-04")

    declarations = {
        "mrp": {"value": "₹ 60.00 (Inclusive of all taxes)", "confidence": 0.95, "status": "FOUND"},
        "net_quantity": {"value": "200 g", "confidence": 0.92, "status": "FOUND"},
        "manufacturer": {"value": "XYZ Foods Pvt. Ltd. Plot No. 123, Kanpur - 208001", "confidence": 0.90, "status": "FOUND"},
        "product_name": {"value": "Moong Dal Namkeen", "confidence": 0.95, "status": "FOUND"},
        "manufacturing_date": {"value": "01/05/2024", "confidence": 0.90, "status": "FOUND"},
        "consumer_care": {"value": "Phone: 1800-123-4567 Email: care@xyzfoods.com", "confidence": 0.88, "status": "FOUND"},
        "country_of_origin": {"value": "INDIA", "confidence": 0.95, "status": "FOUND"},
        "batch_or_lot_number": {"value": "A1234", "confidence": 0.85, "status": "FOUND"}
    }

    eval_result = ComplianceEngine.evaluate(
        inspection_id="insp_test_canonical",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    # Verify canonical requirements count is exactly 7
    canonical_list = eval_result.canonical_requirements
    assert len(canonical_list) == 12  # 7 core + 5 consumer affairs food rules

    # Find MRP canonical requirement
    mrp_reqs = [cr for cr in canonical_list if cr.canonical_id == "REQ-MRP"]
    assert len(mrp_reqs) == 1, "There must be exactly ONE canonical MRP requirement card!"

    mrp_group = mrp_reqs[0]
    assert mrp_group.status == "COMPLIANT"
    assert len(mrp_group.sub_checks) >= 3 # Contains PCR-R6-001, PCR-R6-002, PCR-R6-011

def test_ocr_omission_returns_needs_review_never_false_violation():
    """Verify that unread or omitted OCR field triggers NEEDS_REVIEW, not NON_COMPLIANT."""
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-09-04")

    declarations = {
        "mrp": {"value": "₹ 60.00 (Inclusive of all taxes)", "confidence": 0.95, "status": "FOUND"},
        "net_quantity": {"value": "200 g", "confidence": 0.92, "status": "FOUND"},
        "manufacturer": {"value": "XYZ Foods Pvt. Ltd. Plot No. 123, Kanpur - 208001", "confidence": 0.90, "status": "FOUND"},
        "product_name": {"value": "Moong Dal Namkeen", "confidence": 0.95, "status": "FOUND"},
        "manufacturing_date": {"value": "01/05/2024", "confidence": 0.90, "status": "FOUND"},
        # consumer_care is omitted (perception didn't find it)
        "country_of_origin": {"value": "INDIA", "confidence": 0.95, "status": "FOUND"},
        "batch_or_lot_number": {"value": "A1234", "confidence": 0.85, "status": "FOUND"}
    }

    eval_result = ComplianceEngine.evaluate(
        inspection_id="insp_test_omission",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    assert eval_result.overall_status == "NEEDS_REVIEW"
    assert eval_result.confirmed_violations_count == 0
    assert eval_result.items_needing_review_count >= 1

def test_human_inspector_review_override_flow():
    """Verify that human review override turns NEEDS_REVIEW into COMPLIANT with audit traceability."""
    repo = RegulatoryRepository()
    rules = repo.get_applicable_rules(category="packaged_commodity", inspection_date="2026-09-04")

    declarations = {
        "mrp": {"value": "₹ 60.00 (Inclusive of all taxes)", "confidence": 0.95, "status": "FOUND"},
        "net_quantity": {"value": "200 g", "confidence": 0.92, "status": "FOUND"},
        "manufacturer": {"value": "XYZ Foods Pvt. Ltd. Plot No. 123, Kanpur - 208001", "confidence": 0.90, "status": "FOUND"},
        "product_name": {"value": "Moong Dal Namkeen", "confidence": 0.95, "status": "FOUND"},
        "manufacturing_date": {"value": "01/05/2024", "confidence": 0.90, "status": "FOUND"},
        # consumer_care omitted -> will trigger NEEDS_REVIEW
        "country_of_origin": {"value": "INDIA", "confidence": 0.95, "status": "FOUND"},
        "batch_or_lot_number": {"value": "A1234", "confidence": 0.85, "status": "FOUND"}
    }

    # First evaluation without human review
    initial_res = ComplianceEngine.evaluate(
        inspection_id="insp_test_human_review",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )
    assert initial_res.overall_status == "NEEDS_REVIEW"

    # Inspector reviews REQ-CONSUMER-CARE on physical package
    human_reviews = {
        "REQ-CONSUMER-CARE": {
            "canonical_id": "REQ-CONSUMER-CARE",
            "decision": "COMPLIANT",
            "reason": "Declaration visible on physical package but OCR failed",
            "remarks": "Customer care executive details verified on back panel.",
            "reviewer": "INS-DL-4029"
        }
    }

    reviewed_res = ComplianceEngine.evaluate(
        inspection_id="insp_test_human_review",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1",
        human_reviews=human_reviews
    )

    # Overall status becomes COMPLIANT after human review override
    assert reviewed_res.overall_status == "COMPLIANT"
    assert reviewed_res.confirmed_violations_count == 0
    assert reviewed_res.items_needing_review_count == 0

    # REQ-CONSUMER-CARE is marked COMPLIANT and contains human review metadata
    care_req = next(cr for cr in reviewed_res.canonical_requirements if cr.canonical_id == "REQ-CONSUMER-CARE")
    assert care_req.status == "COMPLIANT"
    assert care_req.human_review is not None
    assert care_req.human_review["reviewer"] == "INS-DL-4029"
