from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mediateca import __version__
from mediateca.api.routers import health, libraries, records, search
from mediateca.core.config import settings
from mediateca.core.db import check_schema
from mediateca.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    try:
        check_schema()
    except Exception:  # noqa: BLE001
        logger.exception("Esquema compartido no disponible o incompatible")
        raise
    yield


app = FastAPI(
    title="Mediateca Madrid",
    description=(
        "Portal alternativo de busqueda de videos, DVD y Blu-ray de las "
        "bibliotecas publicas de la Comunidad de Madrid."
    ),
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api")
app.include_router(records.router, prefix="/api")
app.include_router(libraries.router, prefix="/api")
app.include_router(health.router)


@app.get("/", tags=["raiz"])
def root() -> dict[str, str]:
    return {
        "name": "Mediateca Madrid",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
