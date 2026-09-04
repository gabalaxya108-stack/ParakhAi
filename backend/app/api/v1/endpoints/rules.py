from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.schemas.rules import RuleModel, RuleListResponse
from backend.app.repositories.rule_repository import get_rule_repository
from backend.app.core.logging import get_logger

logger = get_logger("api.rules")
router = APIRouter()

@router.get(
    "/rules/meta/versions",
    summary="List available rule catalog versions",
    description="Returns all codified version tags available in the rule management repository."
)
async def list_rule_versions():
    repo = get_rule_repository()
    versions = repo.get_available_versions()
    return {
        "available_versions": versions,
        "latest_version": repo.get_latest_version()
    }

@router.get(
    "/rules",
    response_model=RuleListResponse,
    summary="Retrieve Legal Metrology rules with versioning and applicability filtering",
    description="Returns a deterministic list of legal compliance rules filtered by catalog version, product category, and declaration field."
)
async def list_rules(
    version: Optional[str] = Query(None, description="Rule catalog version (e.g. '2026.1', '2024.1'). Defaults to latest."),
    category: Optional[str] = Query(None, description="Product category for applicability filtering (e.g. 'food', 'beverages')"),
    field: Optional[str] = Query(None, description="Declaration field to validate (e.g. 'mrp', 'net_quantity')"),
    enabled_only: bool = Query(True, description="Return only enabled rules")
):
    repo = get_rule_repository()
    available = repo.get_available_versions()

    if version and version not in available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule catalog version '{version}' not found. Available versions: {available}"
        )

    selected_version = version or repo.get_latest_version()
    rules = repo.list_rules(
        version=selected_version,
        category=category,
        field=field,
        enabled_only=enabled_only
    )

    return RuleListResponse(
        rules=rules,
        total=len(rules),
        selected_version=selected_version,
        available_versions=available
    )

@router.get(
    "/rules/{rule_id}",
    response_model=RuleModel,
    summary="Retrieve a single Legal Metrology rule by ID",
    description="Returns the exact statutory rule definition, requirements, and severity for a given rule_id."
)
async def get_rule_by_id(
    rule_id: str,
    version: Optional[str] = Query(None, description="Rule catalog version. Defaults to latest.")
):
    repo = get_rule_repository()
    available = repo.get_available_versions()
    if version and version not in available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule catalog version '{version}' not found. Available versions: {available}"
        )

    selected_version = version or repo.get_latest_version()
    rule = repo.get_rule(rule_id=rule_id, version=selected_version)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found in catalog version '{selected_version}'."
        )

    return rule
