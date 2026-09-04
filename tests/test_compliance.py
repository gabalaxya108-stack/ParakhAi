import io
import pytest
from PIL import Image
from backend.app.schemas.rules import RuleModel
from backend.app.schemas.compliance import ComplianceEvaluationResult
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.services.compliance.engine import ComplianceEngine

def get_test_rules() -> list[RuleModel]:
    repo = get_rule_repository()
    return repo.list_rules(version="2026.1", enabled_only=True)

def create_mock_declarations(overrides=None):
    base = {
        "product_name": {
            "field": "product_name",
            "value": "Crunchy Magic Masala Potato Chips",
            "confidence": 0.98,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 100, "width": 400, "height": 50}
        },
        "manufacturer": {
            "field": "manufacturer",
            "value": "Desi Snacks Ltd., Plot 14, Phase II, Industrial Area, Okhla, New Delhi - 110020",
            "confidence": 0.94,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 900, "width": 600, "height": 60}
        },
        "packer": {
            "field": "packer",
            "value": None,
            "confidence": 0.0,
            "source": "ocr",
            "bounding_box": None
        },
        "importer": {
            "field": "importer",
            "value": None,
            "confidence": 0.0,
            "source": "ocr",
            "bounding_box": None
        },
        "net_quantity": {
            "field": "net_quantity",
            "value": "120 g",
            "confidence": 0.96,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 600, "width": 150, "height": 40}
        },
        "mrp": {
            "field": "mrp",
            "value": "MRP ₹40 (inclusive of all taxes)",
            "confidence": 0.97,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 700, "width": 250, "height": 45}
        },
        "packing_date": {
            "field": "packing_date",
            "value": "06/2026",
            "confidence": 0.95,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 800, "width": 150, "height": 40}
        },
        "manufacturing_date": {
            "field": "manufacturing_date",
            "value": None,
            "confidence": 0.0,
            "source": "ocr",
            "bounding_box": None
        },
        "consumer_care": {
            "field": "consumer_care",
            "value": "1800-200-4545 Email: care@desisnacks.com",
            "confidence": 0.93,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 1000, "width": 500, "height": 40}
        },
        "country_of_origin": {
            "field": "country_of_origin",
            "value": "India",
            "confidence": 0.99,
            "source": "ocr",
            "bounding_box": {"x": 400, "y": 600, "width": 200, "height": 40}
        },
        "batch_or_lot_number": {
            "field": "batch_or_lot_number",
            "value": "LOT-2026-B88",
            "confidence": 0.95,
            "source": "ocr",
            "bounding_box": {"x": 400, "y": 800, "width": 200, "height": 40}
        }
    }
    if overrides:
        for k, v in overrides.items():
            base[k] = v
    return base

# 1. Fully compliant example
def test_fully_compliant_example():
    rules = get_test_rules()
    declarations = create_mock_declarations()

    res = ComplianceEngine.evaluate(
        inspection_id="test_compliant",
        extracted_declarations=declarations,
        product_category="food",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    assert res.overall_status == "COMPLIANT"
    assert res.risk_score == 0
    assert len(res.violations) == 0
    assert len(res.checks) == len(rules)
    for check in res.checks:
        assert check.status in ["COMPLIANT", "NOT_APPLICABLE"]

# 2. Missing MRP
def test_missing_mrp_triggers_potential_violation():
    rules = get_test_rules()
    declarations = create_mock_declarations(overrides={
        "mrp": {
            "field": "mrp",
            "value": None,
            "confidence": 0.0,
            "source": "ocr",
            "bounding_box": None
        }
    })

    res = ComplianceEngine.evaluate(
        inspection_id="test_missing_mrp",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    assert res.overall_status in ["NEEDS_REVIEW", "MANUAL_REVIEW"]
    assert res.risk_score > 0

    mrp_check = next((c for c in res.checks if c.rule_id == "LM-MRP-001"), None)
    assert mrp_check is not None
    assert mrp_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW"]
    assert mrp_check.extracted_value is None

# 3. Missing Net Quantity
def test_missing_net_quantity_triggers_potential_violation():
    rules = get_test_rules()
    declarations = create_mock_declarations(overrides={
        "net_quantity": {
            "field": "net_quantity",
            "value": None,
            "confidence": 0.0,
            "source": "ocr",
            "bounding_box": None
        }
    })

    res = ComplianceEngine.evaluate(
        inspection_id="test_missing_net_quantity",
        extracted_declarations=declarations,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    assert res.overall_status in ["NEEDS_REVIEW", "MANUAL_REVIEW"]
    qty_check = next((c for c in res.checks if c.rule_id == "LM-NETQTY-001"), None)
    assert qty_check is not None
    assert qty_check.status in ["NEEDS_REVIEW", "MANUAL_REVIEW"]

# 4. Low-confidence extraction maps to MANUAL_REVIEW (never definitive violation)
def test_low_confidence_maps_to_manual_review():
    rules = get_test_rules()
    declarations = create_mock_declarations(overrides={
        "mrp": {
            "field": "mrp",
            "value": "₹40",
            "confidence": 0.45,  # Below 0.70 threshold!
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 700, "width": 250, "height": 45}
        }
    })

    res = ComplianceEngine.evaluate(
        inspection_id="test_low_conf",
        extracted_declarations=declarations,
        product_category="food",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    # Must be MANUAL_REVIEW, NOT a violation!
    assert res.overall_status in ["MANUAL_REVIEW", "NEEDS_REVIEW"]
    assert len(res.violations) == 0

    mrp_check = next((c for c in res.checks if c.rule_id == "LM-MRP-001"), None)
    assert mrp_check is not None
    assert mrp_check.status in ["MANUAL_REVIEW", "NEEDS_REVIEW"]
    assert mrp_check.detection_status == "UNCLEAR"
    assert "below verification threshold" in mrp_check.reason

# 5. Not-applicable rule check
def test_not_applicable_rule():
    rules = get_test_rules()
    declarations = create_mock_declarations()

    # Category 'electronics' does not require LM-LOT-001 (batch number)
    res = ComplianceEngine.evaluate(
        inspection_id="test_electronics",
        extracted_declarations=declarations,
        product_category="electronics",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    lot_check = next((c for c in res.checks if c.rule_id == "LM-LOT-001"), None)
    assert lot_check is not None
    assert lot_check.status == "NOT_APPLICABLE"
    assert lot_check.detection_status == "NOT_APPLICABLE"

# 6. Non-standard unit specification ('gms' instead of 'g')
def test_non_standard_unit_symbol_violation():
    rules = get_test_rules()
    declarations = create_mock_declarations(overrides={
        "net_quantity": {
            "field": "net_quantity",
            "value": "Net Wt: 120 gms",  # 'gms' is prohibited by Rule 11
            "confidence": 0.96,
            "source": "ocr",
            "bounding_box": {"x": 100, "y": 600, "width": 150, "height": 40}
        }
    })

    res = ComplianceEngine.evaluate(
        inspection_id="test_non_standard_unit",
        extracted_declarations=declarations,
        product_category="food",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    unit_violation = next((v for v in res.violations if v.rule_id == "LM-NETQTY-002"), None)
    assert unit_violation is not None
    assert unit_violation.status in ["POTENTIAL_VIOLATION", "NON_COMPLIANT", "CONFIRMED_VIOLATION"]
    assert "Rule 11 mandates standard symbols" in unit_violation.reason

# 7. Engine Determinism
def test_engine_determinism():
    rules = get_test_rules()
    declarations = create_mock_declarations()

    res1 = ComplianceEngine.evaluate("test_det", declarations, "food", rules, "2026.1")
    res2 = ComplianceEngine.evaluate("test_det", declarations, "food", rules, "2026.1")

    assert res1.overall_status == res2.overall_status
    assert res1.risk_score == res2.risk_score
    assert len(res1.violations) == len(res2.violations)
    assert [c.status for c in res1.checks] == [c.status for c in res2.checks]

# 8. POST /api/v1/inspections/{inspection_id}/evaluate API
def test_post_inspection_evaluate_api(client):
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), color=(200, 200, 200)).save(buf, format="JPEG")
    upload_res = client.post(
        "/api/v1/inspections",
        files={"file": ("comp_test.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert upload_res.status_code == 201
    inspection_id = upload_res.json()["inspection_id"]

    eval_res = client.post(
        f"/api/v1/inspections/{inspection_id}/evaluate?category=packaged_commodity&rule_version=2026.1"
    )
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["inspection_id"] == inspection_id
    assert data["overall_status"] in ["COMPLIANT", "CONFIRMED_VIOLATION", "NON_COMPLIANT", "NEEDS_REVIEW", "POTENTIAL_VIOLATION", "MANUAL_REVIEW"]
    assert "risk_score" in data
    assert "violations" in data
    assert "checks" in data
    assert len(data["checks"]) >= 10

    # Test GET cached compliance
    cached_res = client.get(f"/api/v1/inspections/{inspection_id}/compliance")
    assert cached_res.status_code == 200
    assert cached_res.json()["inspection_id"] == inspection_id
