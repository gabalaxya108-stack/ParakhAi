from typing import Optional, Any
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    timestamp: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
