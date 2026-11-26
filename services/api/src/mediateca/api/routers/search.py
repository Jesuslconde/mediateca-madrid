from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from mediateca.api.aggregation import aggregate_hits_by_obra
from mediateca.api.deps import get_db, get_indexer
from mediateca.api.schemas import SearchResponse
from mediateca.catalog.proximidad import nearby_location_codes, reference_point
from mediateca.catalog.search import CatalogSearch

router = APIRouter(tags=["busqueda"])

SORT_MAP: dict[str, list[str] | None] = {
    "relevancia": None,
    "anio_desc": ["anio:desc", "titulo:asc"],
    "anio_asc": ["anio:asc", "titulo:asc"],
    "titulo_asc": ["titulo:asc"],
    "duracion_asc": ["duracion_min:asc", "titulo:asc"],
}


@router.get("/search", response_model=SearchResponse)
def search(
    request: Request,
    q: str = Query(default="", max_length=250, description="Texto de busqueda"),
    titn: str | None = Query(
        default=None, max_length=32, description="Identificador TITN exacto"
    ),
    soporte: list[str] | None = Query(
        default=None,
        description="Puede repetirse: DVD, Blu-ray, 4K UHD, VHS",
    ),
    genero: str | None = Query(default=None),
    anio_desde: int | None = Query(default=None, ge=1900, le=2100),
    anio_hasta: int | None = Query(default=None, ge=1900, le=2100),
    idioma: str | None = Query(default=None),
    paises_origen: list[str] | None = Query(
        default=None,
        description="Puede repetirse: codigos ISO 3166-1 alfa-2 en mayusculas",
    ),
    biblioteca: str | None = Query(default=None),
    fuente: str | None = Query(default=None),
    cp: str | None = Query(default=None, description="Codigo postal de referencia"),
    radio_km: float | None = Query(
        default=None, gt=0, description="Radio de proximidad en kilometros"
    ),
    excluir: list[str] | None = Query(
        default=None, description="Ubicaciones a excluir, repetible"
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="relevancia"),
    indexer: CatalogSearch = Depends(get_indexer),
    session: Session = Depends(get_db),
) -> SearchResponse:
    if "disponible" in request.query_params:
        raise HTTPException(
            status_code=400,
            detail=(
                "El filtro de disponibilidad ya no esta disponible; "
                "consulta la ficha del OPAC para el estado de prestamo"
            ),
        )
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

    if radio_km is not None:
        if not cp:
            raise HTTPException(status_code=422, detail="radio_km requiere cp")
        if reference_point(cp) is None:
            raise HTTPException(status_code=422, detail="Codigo postal no resoluble")

    ubicaciones: list[str] | None = None
    if cp and radio_km is not None:
        ubicaciones = nearby_location_codes(
            session, cp=cp, radio_km=radio_km, excluir=excluir
        )
        if not ubicaciones:
            return SearchResponse(
                query=q or "",
                page=page,
                limit=limit,
                total=0,
                total_ediciones=0,
                total_pages=1,
                took_ms=0,
                facets={},
                hits=[],
            )

    try:
        result = indexer.search(
            q,
            titn=titn,
            soportes=soporte,
            genero=genero,
            anio_desde=anio_desde,
            anio_hasta=anio_hasta,
            idioma=idioma,
            paises_origen=paises_origen,
            biblioteca=biblioteca,
            fuente=fuente,
            ubicaciones=ubicaciones,
            sort=SORT_MAP[sort],
            page=page,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="El indice de busqueda no esta disponible",
        ) from exc

    result.setdefault("total_ediciones", result.get("total", 0))
    result["hits"] = aggregate_hits_by_obra(
        session,
        result.get("hits", []),
        biblioteca=biblioteca,
        ubicaciones=ubicaciones,
    )
    return SearchResponse(**result)
