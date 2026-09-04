import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.services.compliance.engine import ComplianceEngine
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.schemas.listing_comparison import EcomListingPayload

client = TestClient(app)

def test_unit_sale_price_and_ecom_listing_rule_engine():
    """
    Verifies Rule 6(11) Unit Sale Price and Rule 6(10) E-Commerce Digital Declarations.
    """
    rule_repo = get_rule_repository()
    rules = rule_repo.list_rules()

    # Case 1: Package Net Quantity 140g (> 100g) with declared MRP Rs 40 -> Mathematical USP calculated
    fields = {
        "mrp": {"value": "₹40.00", "confidence": 0.95, "status": "FOUND"},
        "net_quantity": {"value": "140 g", "confidence": 0.90, "status": "FOUND"}
    }
    res = ComplianceEngine.evaluate(
        inspection_id="test_usp",
        extracted_declarations=fields,
        product_category="packaged_commodity",
        applicable_rules=rules,
        rule_version="2026.1"
    )

    usp_check = next((c for c in res.checks if c.rule_id == "LM-USP-001"), None)
    assert usp_check is not None
    assert usp_check.status == "COMPLIANT"
    assert "0.29" in usp_check.extracted_value or "USP" in usp_check.reason

    # Case 2: E-Commerce Listing Comparison with Overpriced Seller (Violation of Sec 36(2))
    listing_data = {
        "marketplace_name": "QuickCommerce App",
        "listed_price": "₹55.00",  # Higher than package MRP ₹40.00
        "listed_net_quantity": "140 g",
        "listed_country_of_origin": "India"
    }

    res_ecom = ComplianceEngine.evaluate(
        inspection_id="test_ecom",
        extracted_declarations=fields,
        product_category="e_commerce_listing",
        applicable_rules=rules,
        rule_version="2026.1",
        listing_data=listing_data
    )

    ecom_check = next((c for c in res_ecom.checks if c.rule_id == "LM-ECOM-001"), None)
    assert ecom_check is not None
    assert ecom_check.status in ["NON_COMPLIANT", "POTENTIAL_VIOLATION"]
    assert "exceeds" in ecom_check.reason.lower()
