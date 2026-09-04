import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, get_logger
from backend.app.core.errors import setup_exception_handlers
from backend.app.core.rate_limiter import InMemoryRateLimiterMiddleware
from backend.app.api.v1.router import api_router

# Initialize structured logging
setup_logging()
logger = get_logger("app.main")

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        debug=settings.DEBUG
    )

    # CORS Middleware with strict origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # In-memory Rate Limiting Middleware
    application.add_middleware(InMemoryRateLimiterMiddleware)

    # Setup Custom Exception Handlers
    setup_exception_handlers(application)

    # Request logging & timing middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration}ms)")
        response.headers["X-Process-Time-Ms"] = str(duration)
        return response

    # Mount Static Uploads Directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    # Include Versioned API Routes
    application.include_router(api_router, prefix=settings.API_V1_STR)


    @application.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "timestamp": time.time()
        }

    @application.get("/", tags=["root"])
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs",
            "health_url": f"{settings.API_V1_STR}/health"
        }


    @application.on_event("startup")
    async def startup_event():
        """Create all database tables on startup."""
        try:
            from backend.app.db.session import engine
            from backend.app.db.base import Base
            import backend.app.models  # noqa: F401 - import all models so Base knows about them
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified successfully.")
        except Exception as e:
            logger.warning(f"Database table creation warning (non-fatal): {e}")

    return application

app = create_application()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)
