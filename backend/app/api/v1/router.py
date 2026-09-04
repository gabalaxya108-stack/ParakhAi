from fastapi import APIRouter
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.inspections import router as inspections_router
from backend.app.api.v1.endpoints.rules import router as rules_router
from backend.app.api.v1.endpoints.analytics import router as analytics_router
from backend.app.api.v1.endpoints.admin import router as admin_router
from backend.app.api.v1.endpoints.system import router as system_router
from backend.app.api.v1.endpoints.regulatory import router as regulatory_router
from backend.app.api.v1.endpoints.assistant import router as assistant_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.complaints import router as complaints_router
from backend.app.api.v1.endpoints.database_monitor import router as db_monitor_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(inspections_router, tags=["inspections"])
api_router.include_router(complaints_router, tags=["complaints"])
api_router.include_router(rules_router, tags=["rules"])
api_router.include_router(analytics_router, tags=["analytics"])
api_router.include_router(admin_router, tags=["admin"])
api_router.include_router(system_router, tags=["system"])
api_router.include_router(db_monitor_router, tags=["database-monitor"])
api_router.include_router(regulatory_router, tags=["regulatory"])
api_router.include_router(assistant_router, tags=["assistant"])
