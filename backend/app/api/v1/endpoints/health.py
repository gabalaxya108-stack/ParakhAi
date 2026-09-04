import time
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.health import HealthCheckResponse

router = APIRouter()
START_TIME = time.time()

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check endpoint",
    description="Returns the operational status, service metadata, and uptime of the backend service."
)
async def get_health():
    uptime = round(time.time() - START_TIME, 2)
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime
    )
