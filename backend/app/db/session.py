from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings
import os

db_url = getattr(settings, "normalized_database_url", settings.DATABASE_URL)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {"pool_pre_ping": True}
if not db_url.startswith("sqlite"):
    try:
        import psycopg2
        engine_kwargs.update({"pool_size": 10, "max_overflow": 20})
    except ImportError:
        # Fallback to sqlite if postgresql driver is not available
        db_url = "sqlite:///./legal_metrology.db"
        engine_kwargs = {"pool_pre_ping": True}

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
