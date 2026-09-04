import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.db.session import get_db
from backend.app.repositories.regulatory_repository import RegulatoryRepository
from backend.app.core.logging import get_logger

logger = get_logger("api.endpoints.system")

router = APIRouter(prefix="/system")

@router.get("/database-health")
def get_database_health(db: Session = Depends(get_db)):
    """
    Returns realtime database connectivity, engine type, checked latency,
    and statutory rule counts from the actual database.
    """
    start_time = time.perf_counter()
    status = "LIVE"
    engine_name = db.bind.dialect.name if db and db.bind else "sqlite"
    
    try:
        # Perform a fast ping query
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status = "DISCONNECTED"
        latency_ms = 0.0

    # Retrieve real counts from regulatory database repository
    repo = RegulatoryRepository()
    summary_dto = repo.get_summary()
    summary = summary_dto.model_dump()

    now_utc = datetime.now(timezone.utc).isoformat()

    return {
        "status": status,
        "database": "postgresql" if "postgres" in engine_name.lower() else "sqlite",
        "engine_dialect": engine_name,
        "environment": "Development",
        "host": "localhost" if "sqlite" in engine_name.lower() else "127.0.0.1",
        "database_name": "parakhai",
        "latency_ms": latency_ms,
        "checked_at": now_utc,
        "metrics": {
            "total_rules": summary["total_rules"],
            "active_rules": summary["active_rules"],
            "pending_rules": summary["pending_rules"],
            "superseded_rules": summary["superseded_rules"],
            "documents_count": summary["documents_count"],
            "amendments_count": summary["amendments_count"],
            "latest_version": summary["latest_version"]
        }
    }


@router.get("/ocr")
def get_ocr_diagnostics():
    from backend.app.services.ocr.tesseract import TesseractOCRProvider
    provider = TesseractOCRProvider()
    try:
        ver = provider.get_version()
        langs = provider.get_installed_languages()
        available = True
    except Exception as e:
        ver = "unknown"
        langs = ["eng"]
        available = False

    return {
        "provider": "tesseract",
        "available": available,
        "version": ver,
        "languages": langs,
        "configured_languages": ["eng", "hin"],
    }
