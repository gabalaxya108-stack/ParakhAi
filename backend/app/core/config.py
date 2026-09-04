import json
from pydantic_settings import BaseSettings
from typing import List, Union
import os
import shutil

class Settings(BaseSettings):
    PROJECT_NAME: str = "PARAKH AI"
    TAGLINE: str = "AI-assisted Legal Metrology Compliance & Inspection Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Ingestion & Storage Directories
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "data/uploads")
    UPLOAD_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "data/uploads")
    FIXTURES_DIR: str = os.getenv("FIXTURES_DIR", "tests/fixtures")
    REPORT_DIR: str = os.getenv("REPORT_DIR", "data/reports")

    # Database Persistence
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/inspections.db")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost:5432/legal_metrology"
    )

    # Tesseract OCR Configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")
    TESSERACT_LANG: str = os.getenv("TESSERACT_LANG", "eng+hin")

    # OCR Configuration: "tesseract" | "mock" | "azure_vision"
    # Defaults to real local tesseract if detected on system PATH or via TESSERACT_CMD
    _has_tesseract: bool = bool(shutil.which("tesseract") or os.getenv("TESSERACT_CMD"))
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "tesseract" if _has_tesseract else "mock")

    AZURE_VISION_ENDPOINT: str = os.getenv("AZURE_VISION_ENDPOINT", "")
    AZURE_VISION_KEY: str = os.getenv("AZURE_VISION_KEY", "")

    # AI Declaration Extraction Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq")
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "groq")
    VISION_AI_MODEL: str = os.getenv("VISION_AI_MODEL", "qwen/qwen3.8-27b")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROK_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    GROQ_CHAT_MODEL: str = os.getenv("GROQ_CHAT_MODEL", "qwen/qwen3.8-27b")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]


    @property
    def normalized_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def cors_origins(self) -> List[str]:
        raw = os.getenv("BACKEND_CORS_ORIGINS") or os.getenv("CORS_ORIGINS") or self.BACKEND_CORS_ORIGINS
        if isinstance(raw, list):
            origins = list(raw)
        elif isinstance(raw, str):
            raw_str = raw.strip()
            if raw_str.startswith("[") and raw_str.endswith("]"):
                try:
                    origins = json.loads(raw_str)
                except Exception:
                    origins = [x.strip().strip("'\"") for x in raw_str.strip("[]").split(",") if x.strip()]
            else:
                origins = [x.strip().strip("'\"") for x in raw_str.split(",") if x.strip()]
        else:
            origins = list(self.BACKEND_CORS_ORIGINS)

        frontend_url = os.getenv("FRONTEND_URL", "").strip()
        if frontend_url and frontend_url not in origins:
            origins.append(frontend_url)

        return origins


    def model_post_init(self, __context) -> None:
        key = self.GROK_API_KEY or self.GROQ_API_KEY or os.getenv("GROK_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        if key:
            object.__setattr__(self, "GROK_API_KEY", key)
            object.__setattr__(self, "GROQ_API_KEY", key)

    class Config:
        case_sensitive = True
        env_file = ("backend/.env", ".env")
        extra = "ignore"

settings = Settings()
