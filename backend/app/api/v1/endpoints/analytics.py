from typing import Optional
from fastapi import APIRouter, Query
from backend.app.schemas.analytics import ManufacturerAnalyticsResponse
from backend.app.services.analytics.service import ManufacturerAnalyticsService
from backend.app.core.logging import get_logger

logger = get_logger("api.analytics")
router = APIRouter()

@router.get(
    "/analytics/manufacturers",
    response_model=ManufacturerAnalyticsResponse,
    summary="Retrieve manufacturer-level statutory compliance analytics",
    description="Aggregates historical inspection data across manufacturers with repeated issues breakdown. Adheres strictly to non-defamatory, statutorily neutral language (e.g. 'Repeated potential issues detected'). Supports filtering by date range, manufacturer, product category, and violation type."
)
async def get_manufacturer_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format, e.g. '2026-01-01')"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format, e.g. '2026-12-31')"),
    manufacturer: Optional[str] = Query(None, description="Manufacturer name substring filter"),
    product_category: Optional[str] = Query(None, description="Product category filter (e.g. 'food', 'packaged_commodity')"),
    violation_type: Optional[str] = Query(None, description="Violation type filter (e.g. 'MISSING_DECLARATION')")
):
    logger.info(f"Retrieving manufacturer analytics (mfr='{manufacturer}', category='{product_category}', viol='{violation_type}')")

    return ManufacturerAnalyticsService.get_manufacturer_analytics(
        start_date=start_date,
        end_date=end_date,
        manufacturer_filter=manufacturer,
        category_filter=product_category,
        violation_type_filter=violation_type
    )
