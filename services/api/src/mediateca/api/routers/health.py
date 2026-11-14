from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from mediateca import __version__
from mediateca.api.deps import get_db
from mediateca.api.schemas import HealthResponse
from mediateca.core.search import get_meili_client

router = APIRouter(tags=["salud"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_db)) -> HealthResponse:
    database = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        database = "error"

    meilisearch = "ok"
    try:
        payload = get_meili_client().health()
        if payload.get("status") not in {"available", "ok"}:
            meilisearch = "degraded"
    except Exception:  # noqa: BLE001
        meilisearch = "error"

    status = "ok" if database == "ok" and meilisearch == "ok" else "degraded"
    return HealthResponse(
        status=status,
        database=database,
        meilisearch=meilisearch,
        version=__version__,
    )
