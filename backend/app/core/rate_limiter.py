import time
from typing import Dict, List, Tuple
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("core.rate_limiter")

class InMemoryRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter protecting APIs from automated abuse,
    Denial of Service, and burst traffic while permitting ordinary usage.
    """
    def __init__(self, app, max_requests_per_minute: int = 300, upload_limit_per_minute: int = 100):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.upload_limit = upload_limit_per_minute
        # Dict mapping client_ip -> list of timestamps
        self.requests_history: Dict[str, List[float]] = {}
        self.upload_history: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        one_minute_ago = now - 60.0

        # Skip rate limiting for test runner, static assets, or health checks
        path = request.url.path
        if (
            client_ip == "testclient"
            or getattr(settings, "ENVIRONMENT", "").lower() in ("testing", "test")
            or path.startswith("/uploads")
            or path == "/api/v1/health"
            or path == "/"
        ):
            return await call_next(request)

        # 1. Check Upload Rate Limits
        if request.method == "POST" and (path.endswith("/inspections") or path.endswith("/batch")):
            if client_ip not in self.upload_history:
                self.upload_history[client_ip] = []
            
            # Prune old entries
            self.upload_history[client_ip] = [t for t in self.upload_history[client_ip] if t > one_minute_ago]

            if len(self.upload_history[client_ip]) >= self.upload_limit:
                logger.warning(f"Rate limit exceeded for uploads by {client_ip} ({len(self.upload_history[client_ip])} uploads/min)")
                return Response(
                    content='{"error":"RATE_LIMIT_EXCEEDED","detail":"Upload rate limit exceeded. Please slow down.","retry_after_seconds":60}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={"Retry-After": "60"}
                )
            self.upload_history[client_ip].append(now)

        # 2. Check General API Rate Limits
        if client_ip not in self.requests_history:
            self.requests_history[client_ip] = []

        self.requests_history[client_ip] = [t for t in self.requests_history[client_ip] if t > one_minute_ago]

        if len(self.requests_history[client_ip]) >= self.max_requests:
            logger.warning(f"General API rate limit exceeded by {client_ip} ({len(self.requests_history[client_ip])} req/min)")
            return Response(
                content='{"error":"RATE_LIMIT_EXCEEDED","detail":"Too many requests. Please slow down.","retry_after_seconds":60}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": "60"}
            )
        self.requests_history[client_ip].append(now)

        return await call_next(request)
