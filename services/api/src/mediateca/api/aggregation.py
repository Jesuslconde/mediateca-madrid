from __future__ import annotations

from collections import defaultdict
from typing import Any

from mediateca_shared.models import Edicion, Ejemplar
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


def _soportes(ediciones: list[Edicion]) -> list[str]:
    values: set[str] = set()
    for edicion in ediciones:
        values.update(edicion.soportes or [])
        for ejemplar in edicion.ejemplares:
            if ejemplar.soporte:
                values.add(ejemplar.soporte)
    return sorted(values)


def _bibliotecas(ediciones: list[Edicion]) -> list[str]:
    values: set[str] = set()
    for edicion in ediciones:
        for ejemplar in edicion.ejemplares:
            if ejemplar.biblioteca is not None:
                values.add(ejemplar.biblioteca.nombre)
    return sorted(values)


def _primer_valor(ediciones: list[Edicion], atributo: str) -> Any:
    for edicion in ediciones:
        value = getattr(edicion, atributo)
        if value not in (None, "", []):
            return value
    return None


def aggregate_hits_by_obra(session: Session, hits: list[dict[str, Any]]) -> None:
    """Agrega soportes, bibliotecas y ejemplares de todas las ediciones de la obra."""
    obra_ids = sorted(
        {
            int(hit["obra_id"])
            for hit in hits
            if hit.get("obra_id") is not None
        }
    )
    if not obra_ids:
        for hit in hits:
            hit["ediciones_count"] = 1
        return

    stmt = (
        select(Edicion)
        .where(Edicion.obra_id.in_(obra_ids))
        .options(
            selectinload(Edicion.fuente),
            selectinload(Edicion.obra),
            selectinload(Edicion.ejemplares).selectinload(Ejemplar.biblioteca),
        )
    )
    by_obra: dict[int, list[Edicion]] = defaultdict(list)
    for edicion in session.scalars(stmt):
        if edicion.obra_id is not None:
            by_obra[edicion.obra_id].append(edicion)

    for hit in hits:
        obra_id = hit.get("obra_id")
        if obra_id is None:
            hit["ediciones_count"] = 1
            continue
        ediciones = by_obra.get(int(obra_id), [])
        if not ediciones:
            hit["ediciones_count"] = 1
            continue

        hit["ediciones_count"] = len(ediciones)
        hit["soportes"] = _soportes(ediciones)
        hit["bibliotecas"] = _bibliotecas(ediciones)
        hit["ejemplares"] = sum(len(edicion.ejemplares) for edicion in ediciones)
        hit["obra_titulo"] = hit.get("obra_titulo") or _primer_valor(
            ediciones, "titulo_uniforme"
        )
        for atributo in (
            "tmdb_poster_url",
            "anio",
            "duracion_min",
            "sinopsis",
            "titulo_uniforme",
        ):
            if not hit.get(atributo):
                value = _primer_valor(ediciones, atributo)
                if value not in (None, "", []):
                    hit[atributo] = value
