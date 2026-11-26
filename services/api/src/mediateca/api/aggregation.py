from __future__ import annotations

from collections import defaultdict
from typing import Any

from mediateca_shared.identity import normalize_location_code
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


def _parse_location_code(code: str) -> tuple[str, str, str] | None:
    """Parsea ``b:<fuente>:<codigo>`` / ``s:<fuente>:<codigo>`` o devuelve ``None``."""
    raw = normalize_location_code(code)
    partes = raw.split(":")
    if len(partes) != 3 or partes[0] not in ("b", "s"):
        return None
    return partes[0], partes[1], partes[2]


def _matching_ejemplares(edicion: Edicion, biblioteca: str) -> list[Ejemplar]:
    """Ejemplares de la edicion que coinciden con el filtro de biblioteca/sucursal."""
    parsed = _parse_location_code(biblioteca)
    if parsed is None:
        # Filtro por nombre: red (bibliotecas) o sucursal (ubicaciones_texto).
        return [
            ejemplar
            for ejemplar in edicion.ejemplares
            if (ejemplar.biblioteca is not None and ejemplar.biblioteca.nombre == biblioteca)
            or ejemplar.sucursal_nombre == biblioteca
        ]

    kind, fuente, codigo = parsed
    edicion_fuente = edicion.fuente.codigo if edicion.fuente is not None else "madrid"
    if edicion_fuente != fuente:
        return []

    if kind == "b":
        return [
            ejemplar
            for ejemplar in edicion.ejemplares
            if ejemplar.biblioteca is not None and ejemplar.biblioteca.codigo == codigo
        ]
    return [
        ejemplar
        for ejemplar in edicion.ejemplares
        if ejemplar.sucursal_codigo == codigo
    ]


def _matching_ediciones(
    ediciones: list[Edicion], biblioteca: str
) -> list[tuple[Edicion, list[Ejemplar]]]:
    """Ediciones con al menos un ejemplar en la biblioteca/sucursal seleccionada."""
    result: list[tuple[Edicion, list[Ejemplar]]] = []
    for edicion in ediciones:
        ejemplares = _matching_ejemplares(edicion, biblioteca)
        if ejemplares:
            result.append((edicion, ejemplares))
    return result


def _matching_ejemplares_set(edicion: Edicion, allowed: set[str]) -> list[Ejemplar]:
    """Ejemplares de la edicion cuya ubicacion esta en el conjunto permitido."""
    fuente = edicion.fuente.codigo if edicion.fuente is not None else "madrid"
    result: list[Ejemplar] = []
    for ejemplar in edicion.ejemplares:
        if ejemplar.sucursal_codigo and f"s:{fuente}:{ejemplar.sucursal_codigo}" in allowed:
            result.append(ejemplar)
        elif (
            ejemplar.biblioteca is not None
            and f"b:{fuente}:{ejemplar.biblioteca.codigo}" in allowed
        ):
            result.append(ejemplar)
    return result


def _matching_ediciones_set(
    ediciones: list[Edicion], allowed: set[str]
) -> list[tuple[Edicion, list[Ejemplar]]]:
    """Ediciones con al menos un ejemplar en el conjunto de ubicaciones permitidas."""
    result: list[tuple[Edicion, list[Ejemplar]]] = []
    for edicion in ediciones:
        ejemplares = _matching_ejemplares_set(edicion, allowed)
        if ejemplares:
            result.append((edicion, ejemplares))
    return result


def _soportes_filtrados(matching: list[tuple[Edicion, list[Ejemplar]]]) -> list[str]:
    values: set[str] = set()
    for edicion, ejemplares in matching:
        values.update(edicion.soportes or [])
        for ejemplar in ejemplares:
            if ejemplar.soporte:
                values.add(ejemplar.soporte)
    return sorted(values)


def _bibliotecas_filtradas(matching: list[tuple[Edicion, list[Ejemplar]]]) -> list[str]:
    values: set[str] = set()
    for _, ejemplares in matching:
        for ejemplar in ejemplares:
            if ejemplar.biblioteca is not None:
                values.add(ejemplar.biblioteca.nombre)
    return sorted(values)


def aggregate_hits_by_obra(
    session: Session,
    hits: list[dict[str, Any]],
    *,
    biblioteca: str | None = None,
    ubicaciones: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Agrega soportes, bibliotecas y ejemplares de las ediciones de la obra.

    Cuando hay un filtro de biblioteca o sucursal activo, solo se cuentan los
    ejemplares que coinciden con el filtro y se descartan las obras que no tienen
    al menos un ejemplar en la ubicacion seleccionada. Con un conjunto de
    ubicaciones permitidas (proximidad), se cuentan solo los ejemplares situados
    en ese conjunto.
    """
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
        return hits

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

    kept: list[dict[str, Any]] = []
    for hit in hits:
        obra_id = hit.get("obra_id")
        if obra_id is None:
            hit["ediciones_count"] = 1
            kept.append(hit)
            continue
        ediciones = by_obra.get(int(obra_id), [])
        if not ediciones:
            hit["ediciones_count"] = 1
            kept.append(hit)
            continue

        matching: list[tuple[Edicion, list[Ejemplar]]] | None = None
        if ubicaciones is not None:
            matching = _matching_ediciones_set(ediciones, set(ubicaciones))
        elif biblioteca:
            matching = _matching_ediciones(ediciones, biblioteca)

        if matching is not None:
            if not matching:
                # Sin ejemplares en la ubicacion seleccionada: no se muestra.
                continue
            hit["ediciones_count"] = len(matching)
            hit["soportes"] = _soportes_filtrados(matching)
            hit["bibliotecas"] = _bibliotecas_filtradas(matching)
            hit["ejemplares"] = sum(len(ejemplares) for _, ejemplares in matching)
        else:
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
        kept.append(hit)

    return kept
