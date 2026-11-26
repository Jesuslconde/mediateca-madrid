from __future__ import annotations

from mediateca_shared.geo import centroide, haversine_km
from mediateca_shared.identity import normalize_location_code
from mediateca_shared.models import Biblioteca, Fuente, Sucursal
from sqlalchemy import select
from sqlalchemy.orm import Session


def reference_point(codigo_postal: str | None) -> tuple[float, float] | None:
    """Resuelve el centroide de referencia de un codigo postal, o None."""
    item = centroide(codigo_postal)
    if item is None:
        return None
    return item.latitud, item.longitud


def location_point(
    latitud: float | None,
    longitud: float | None,
    codigo_postal: str | None,
) -> tuple[float, float] | None:
    """Punto (latitud, longitud) de una ubicacion, con respaldo en el CP."""
    if latitud is not None and longitud is not None:
        return latitud, longitud
    if codigo_postal:
        item = centroide(codigo_postal)
        if item is not None:
            return item.latitud, item.longitud
    return None


def _parse_exclusions(
    excluir: list[str] | None,
) -> tuple[set[str], set[tuple[str, str]]]:
    """Devuelve (codigos_s, bibliotecas_b) normalizados de las exclusiones."""
    excluir_s: set[str] = set()
    excluir_b: set[tuple[str, str]] = set()
    for raw in excluir or []:
        code = normalize_location_code(raw)
        partes = code.split(":")
        if len(partes) != 3 or partes[0] not in ("s", "b"):
            continue
        if partes[0] == "s":
            excluir_s.add(code)
        else:
            excluir_b.add((partes[1], partes[2]))
    return excluir_s, excluir_b


def nearby_location_codes(
    session: Session,
    *,
    cp: str | None,
    radio_km: float,
    excluir: list[str] | None = None,
) -> list[str]:
    """Codigos de ubicacion dentro del radio, menos las exclusiones.

    Devuelve codigos ``s:<fuente>:<sucursal>`` de sucursales cercanas y
    ``b:<fuente>:<biblioteca>`` de bibliotecas sin sucursales cercanas.
    """
    ref = reference_point(cp)
    if ref is None:
        return []

    excluir_s, excluir_b = _parse_exclusions(excluir)

    allowed: list[str] = []

    sucursales = session.execute(
        select(
            Fuente.codigo.label("fuente"),
            Sucursal.codigo,
            Sucursal.codigo_postal,
            Sucursal.latitud,
            Sucursal.longitud,
            Biblioteca.codigo.label("biblioteca_codigo"),
        )
        .join(Fuente, Fuente.id == Sucursal.fuente_id)
        .join(Biblioteca, Biblioteca.id == Sucursal.biblioteca_id)
    )
    for row in sucursales:
        point = location_point(row.latitud, row.longitud, row.codigo_postal)
        if point is None:
            continue
        if haversine_km(ref[0], ref[1], point[0], point[1]) > radio_km:
            continue
        code = f"s:{row.fuente}:{row.codigo}"
        if code in excluir_s:
            continue
        if (row.fuente, row.biblioteca_codigo) in excluir_b:
            continue
        allowed.append(code)

    subquery = select(Sucursal.id).where(Sucursal.biblioteca_id == Biblioteca.id)
    bibliotecas = session.execute(
        select(
            Fuente.codigo.label("fuente"),
            Biblioteca.codigo,
            Biblioteca.codigo_postal,
            Biblioteca.latitud,
            Biblioteca.longitud,
        )
        .join(Fuente, Fuente.id == Biblioteca.fuente_id)
        .where(~subquery.exists())
    )
    for row in bibliotecas:
        point = location_point(row.latitud, row.longitud, row.codigo_postal)
        if point is None:
            continue
        if haversine_km(ref[0], ref[1], point[0], point[1]) > radio_km:
            continue
        if (row.fuente, row.codigo) in excluir_b:
            continue
        allowed.append(f"b:{row.fuente}:{row.codigo}")

    return allowed
