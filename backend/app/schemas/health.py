from pydantic import BaseModel

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    uptime_seconds: float
