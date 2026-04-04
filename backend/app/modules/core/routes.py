from fastapi import APIRouter
from sqlalchemy import text

from app.config.base import get_settings
from app.extensions.db import SessionLocal
from app.schemas.core import HealthResponse

router = APIRouter(tags=["core"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    database_status = "connected"

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    return HealthResponse(
        status="OK",
        service=settings.app_name,
        version=settings.app_version,
        database=database_status,
    )
