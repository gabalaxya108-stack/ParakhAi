from typing import List
from fastapi import APIRouter
from backend.app.schemas.rules import RuleDefinition
from backend.app.services.rule_engine.catalog import CODIFIED_RULES

router = APIRouter(prefix="/rules", tags=["rules"])

@router.get("", response_model=List[RuleDefinition])
async def list_codified_rules():
    """Returns the full catalog of codified Legal Metrology rules with statutory citations and penalties."""
    return CODIFIED_RULES
