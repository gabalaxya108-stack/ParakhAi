from typing import Dict, Any
from fastapi import APIRouter
from backend.app.db.repository import InspectionRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary():
    """Returns KPI counters, compliance rates, and top violation breakdowns."""
    return InspectionRepository.get_analytics_summary()
