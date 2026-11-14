from __future__ import annotations

import math
from typing import Any

from mediateca.core.config import settings
from mediateca.core.search import get_index, get_meili_client

FACET_FIELDS = ["soportes", "generos", "anio", "idioma", "paises_origen", "bibliotecas"]
ENRICHED_FILTER = "detail_complete = true"


def _quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_filters(
    *,
    soportes: list[str] | None = None,
    genero: str | None = None,
    anio_desde: int | None = None,
    anio_hasta: int | None = None,
    idioma: str | None = None,
    paises_origen: list[str] | None = None,
    biblioteca: str | None = None,
) -> str | None:
    filters: list[str] = []

    if soportes:
        filters.append(
            "(" + " OR ".join(f"soportes = {_quote(item)}" for item in soportes) + ")"
        )
    if genero:
        filters.append(f"generos = {_quote(genero)}")
    if idioma:
        filters.append(f"idioma = {_quote(idioma)}")
    if paises_origen:
        filters.append(
            "("
            + " OR ".join(f"paises_origen = {_quote(item)}" for item in paises_origen)
            + ")"
        )
    if biblioteca:
        filters.append(f"bibliotecas = {_quote(biblioteca)}")
    if anio_desde is not None:
        filters.append(f"anio >= {int(anio_desde)}")
    if anio_hasta is not None:
        filters.append(f"anio <= {int(anio_hasta)}")

    return " AND ".join(filters) if filters else None


class CatalogSearch:
    """Adaptador de busqueda de solo lectura sobre el indice compartido."""

    def __init__(self) -> None:
        self.client = get_meili_client()
        self.index = get_index()

    def search(
        self,
        query: str,
        *,
        soportes: list[str] | None = None,
        genero: str | None = None,
        anio_desde: int | None = None,
        anio_hasta: int | None = None,
        idioma: str | None = None,
        paises_origen: list[str] | None = None,
        biblioteca: str | None = None,
        sort: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = build_filters(
            soportes=soportes,
            genero=genero,
            anio_desde=anio_desde,
            anio_hasta=anio_hasta,
            idioma=idioma,
            paises_origen=paises_origen,
            biblioteca=biblioteca,
        )
        options: dict[str, Any] = {
            "page": max(1, page),
            "hitsPerPage": max(1, min(limit, 100)),
            "facets": FACET_FIELDS,
            "attributesToHighlight": ["titulo", "sinopsis"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>",
        }
        active_filters = [ENRICHED_FILTER]
        if filters:
            active_filters.append(filters)
        options["filter"] = " AND ".join(active_filters)
        if sort:
            options["sort"] = [sort]

        result = self.index.search(query or "", options)
        hits = result.get("hits", [])
        total = result.get("estimatedTotalHits", result.get("totalHits", len(hits)))
        return {
            "query": query or "",
            "page": max(1, page),
            "limit": max(1, min(limit, 100)),
            "total": total,
            "total_pages": max(1, math.ceil(total / max(1, limit))),
            "took_ms": result.get("processingTimeMs", 0),
            "facets": result.get("facetDistribution", {}),
            "hits": hits,
        }

    def health(self) -> dict[str, Any]:
        return self.client.health()


def index_name() -> str:
    return settings.meilisearch_index
