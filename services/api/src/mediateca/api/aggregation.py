from __future__ import annotations

from typing import Any

from mediateca_shared.models import Edicion, Ejemplar
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


def _first_present(values: list[Any]) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def aggregate_hits(
    session: Session, hits: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Enriquece los hits agrupados con los datos de todas las ediciones de la obra."""
    if not hits:
        return []

    obra_ids = {hit.get("obra_id") for hit in hits if hit.get("obra_id") is not None}
    ediciones_por_obra: dict[int, list[Edicion]] = {}
    if obra_ids:
        stmt = (
            select(Edicion)
            .where(Edicion.obra_id.in_(obra_ids))
            .options(
                selectinload(Edicion.obra),
                selectinload(Edicion.ejemplares).selectinload(Ejemplar.biblioteca),
            )
        )
        for edicion in session.scalars(stmt):
            ediciones_por_obra.setdefault(edicion.obra_id, []).append(edicion)

    enriched: list[dict[str, Any]] = []
    for hit in hits:
        item = dict(hit)
        obra_id = item.get("obra_id")
        if obra_id is None:
            item["ediciones_count"] = 1
            enriched.append(item)
            continue

        ediciones = ediciones_por_obra.get(obra_id, [])
        item["ediciones_count"] = len(ediciones) or 1

        soportes: list[str] = []
        bibliotecas: list[str] = []
        ejemplares = 0
        for edicion in ediciones:
            for soporte in edicion.soportes or []:
                if soporte not in soportes:
                    soportes.append(soporte)
            for ejemplar in edicion.ejemplares:
                if ejemplar.biblioteca is not None:
                    nombre = ejemplar.biblioteca.nombre
                    if nombre and nombre not in bibliotecas:
                        bibliotecas.append(nombre)
                ejemplares += 1

        item["soportes"] = soportes or item.get("soportes") or []
        item["bibliotecas"] = sorted(bibliotecas) or item.get("bibliotecas") or []
        item["ejemplares"] = ejemplares

        if ediciones:
            obra = ediciones[0].obra
            item["obra_titulo"] = item.get("obra_titulo") or (
                obra.titulo_uniforme if obra is not None else None
            )
            for campo in ("tmdb_poster_url", "tmdb_url", "sinopsis"):
                if not item.get(campo):
                    valor = _first_present([getattr(edicion, campo) for edicion in ediciones])
                    if valor:
                        item[campo] = valor
            for campo in ("anio", "duracion_min"):
                if item.get(campo) is None:
                    valor = _first_present([getattr(edicion, campo) for edicion in ediciones])
                    if valor is not None:
                        item[campo] = valor

        enriched.append(item)

    return enriched
