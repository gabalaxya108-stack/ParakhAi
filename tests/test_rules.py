import pytest
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.schemas.rules import RuleModel

def test_rule_repository_loading():
    repo = get_rule_repository()
    versions = repo.get_available_versions()
    assert "2026.1" in versions
    assert "2024.1" in versions
    assert repo.get_latest_version() == "2026.1"

    # Fetch 2026.1 rules
    rules_2026 = repo.list_rules(version="2026.1")
    assert len(rules_2026) >= 10
    
    # Check LM-MRP-001 matches specification
    mrp_rule = repo.get_rule("LM-MRP-001", version="2026.1")
    assert mrp_rule is not None
    assert mrp_rule.rule_id == "LM-MRP-001"
    assert mrp_rule.field_to_validate == "mrp"
    assert mrp_rule.validation_type == "REQUIRED"
    assert mrp_rule.rule_version == "2026.1"
    assert "Rule 6(1)(e)" in mrp_rule.source_reference
    assert mrp_rule.enabled is True

def test_get_rules_api_default_version(client):
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert data["selected_version"] == "2026.1"
    assert data["total"] >= 10
    assert len(data["rules"]) == data["total"]

    # Verify every rule preserves the full required model structure
    for r in data["rules"]:
        assert "rule_id" in r
        assert "name" in r
        assert "description" in r
        assert "requirement" in r
        assert "applicable_product_categories" in r
        assert "field_to_validate" in r
        assert "validation_type" in r
        assert "severity" in r
        assert "effective_from" in r
        assert "rule_version" in r
        assert "source_reference" in r
        assert "enabled" in r

def test_rule_version_selection(client):
    # Version 2024.1
    res_2024 = client.get("/api/v1/rules?version=2024.1")
    assert res_2024.status_code == 200
    data_2024 = res_2024.json()
    assert data_2024["selected_version"] == "2024.1"
    assert data_2024["total"] == 2
    for r in data_2024["rules"]:
        assert r["rule_version"] == "2024.1"

    # Version 2026.1
    res_2026 = client.get("/api/v1/rules?version=2026.1")
    assert res_2026.status_code == 200
    data_2026 = res_2026.json()
    assert data_2026["selected_version"] == "2026.1"
    assert data_2026["total"] >= 10

def test_applicability_filtering_by_category(client):
    # Category: 'food' should return rules applicable to 'all' or 'food'
    res_food = client.get("/api/v1/rules?version=2026.1&category=food")
    assert res_food.status_code == 200
    food_rules = res_food.json()["rules"]

    # Category: 'electronics' should return rules with 'all', but not food-specific rules
    res_elec = client.get("/api/v1/rules?version=2026.1&category=electronics")
    assert res_elec.status_code == 200
    elec_rules = res_elec.json()["rules"]

    # LM-LOT-001 is for food/beverages/pharmaceuticals, not electronics
    food_rule_ids = [r["rule_id"] for r in food_rules]
    elec_rule_ids = [r["rule_id"] for r in elec_rules]
    assert "LM-LOT-001" in food_rule_ids
    assert "LM-LOT-001" not in elec_rule_ids

def test_filtering_by_field_to_validate(client):
    res_mrp = client.get("/api/v1/rules?version=2026.1&field=mrp")
    assert res_mrp.status_code == 200
    mrp_rules = res_mrp.json()["rules"]
    assert len(mrp_rules) >= 2
    for r in mrp_rules:
        assert r["field_to_validate"] == "mrp"

    res_netqty = client.get("/api/v1/rules?version=2026.1&field=net_quantity")
    assert res_netqty.status_code == 200
    netqty_rules = res_netqty.json()["rules"]
    assert len(netqty_rules) >= 2
    for r in netqty_rules:
        assert r["field_to_validate"] == "net_quantity"

def test_get_rule_by_id_success(client):
    response = client.get("/api/v1/rules/LM-MRP-001")
    assert response.status_code == 200
    rule = response.json()
    assert rule["rule_id"] == "LM-MRP-001"
    assert rule["name"] == "MRP Mandatory Declaration"
    assert rule["field_to_validate"] == "mrp"
    assert rule["validation_type"] == "REQUIRED"

def test_get_rule_by_id_with_version(client):
    response = client.get("/api/v1/rules/LM-MRP-001?version=2024.1")
    assert response.status_code == 200
    rule = response.json()
    assert rule["rule_id"] == "LM-MRP-001"
    assert rule["rule_version"] == "2024.1"

def test_get_rule_by_id_not_found(client):
    response = client.get("/api/v1/rules/LM-NONEXISTENT-999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_get_rule_versions_meta(client):
    response = client.get("/api/v1/rules/meta/versions")
    assert response.status_code == 200
    data = response.json()
    assert "available_versions" in data
    assert "latest_version" in data
    assert "2026.1" in data["available_versions"]
    assert data["latest_version"] == "2026.1"
