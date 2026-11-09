from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from mediateca.api.deps import get_indexer
from mediateca.api.schemas import SearchResponse
from mediateca.catalog.indexer import MeiliIndexer

router = APIRouter(tags=["busqueda"])

SORT_MAP: dict[str, str | None] = {
    "relevancia": None,
    "anio_desc": "anio:desc",
    "anio_asc": "anio:asc",
    "titulo_asc": "titulo:asc",
    "duracion_asc": "duracion_min:asc",
}


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(default="", max_length=250, description="Texto de busqueda"),
    soporte: list[str] | None = Query(
        default=None,
        description="Puede repetirse: DVD, Blu-ray, 4K UHD, VHS",
    ),
    genero: str | None = Query(default=None),
    anio_desde: int | None = Query(default=None, ge=1900, le=2100),
    anio_hasta: int | None = Query(default=None, ge=1900, le=2100),
    idioma: str | None = Query(default=None),
    biblioteca: str | None = Query(default=None),
    disponible: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="relevancia"),
    indexer: MeiliIndexer = Depends(get_indexer),
) -> SearchResponse:
    if sort not in SORT_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Orden no valido. Valores permitidos: {sorted(SORT_MAP)}",
        )
    if anio_desde and anio_hasta and anio_desde > anio_hasta:
        raise HTTPException(
            status_code=400,
            detail="anio_desde no puede ser mayor que anio_hasta",
        )

    try:
        result = indexer.search(
            q,
            soportes=soporte,
            genero=genero,
            anio_desde=anio_desde,
            anio_hasta=anio_hasta,
            idioma=idioma,
            biblioteca=biblioteca,
            disponible=disponible,
            sort=SORT_MAP[sort],
            page=page,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="El indice de busqueda no esta disponible",
        ) from exc

    return SearchResponse(**result)
