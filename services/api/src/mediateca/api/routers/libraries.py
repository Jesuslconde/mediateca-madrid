from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, Sucursal
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mediateca.api.deps import get_db
from mediateca.api.schemas import LibraryOut, LocationOut, StatsResponse

router = APIRouter(tags=["bibliotecas"])


@router.get("/libraries", response_model=list[LibraryOut])
def list_libraries(session: Session = Depends(get_db)) -> list[LibraryOut]:
    stmt = (
        select(
            Fuente.codigo.label("fuente"),
            Biblioteca.codigo,
            Biblioteca.nombre,
            Biblioteca.municipio,
            func.count(Ejemplar.id).label("ejemplares"),
        )
        .join(Fuente, Fuente.id == Biblioteca.fuente_id)
        .outerjoin(Ejemplar, Ejemplar.biblioteca_id == Biblioteca.id)
        .group_by(Biblioteca.id, Fuente.codigo)
        .order_by(Biblioteca.nombre)
    )
    return [
        LibraryOut(
            fuente=row.fuente,
            codigo=row.codigo,
            nombre=row.nombre,
            municipio=row.municipio,
            ejemplares=row.ejemplares,
        )
        for row in session.execute(stmt)
    ]


@router.get("/locations", response_model=list[LocationOut])
def list_locations(session: Session = Depends(get_db)) -> list[LocationOut]:
    libraries_stmt = (
        select(
            Fuente.codigo.label("fuente"),
            Biblioteca.codigo,
            Biblioteca.nombre,
            Biblioteca.municipio,
            func.count(Ejemplar.id).label("ejemplares"),
        )
        .join(Fuente, Fuente.id == Biblioteca.fuente_id)
        .outerjoin(Ejemplar, Ejemplar.biblioteca_id == Biblioteca.id)
        .group_by(Biblioteca.id, Fuente.codigo)
    )
    branches_stmt = (
        select(
            Fuente.codigo.label("fuente"),
            Biblioteca.codigo.label("biblioteca_codigo"),
            Biblioteca.nombre.label("biblioteca_nombre"),
            Ejemplar.sucursal_codigo.label("sucursal_codigo"),
            func.max(Ejemplar.sucursal_nombre).label("sucursal_nombre"),
            func.max(Sucursal.municipio).label("sucursal_municipio"),
            func.max(Biblioteca.municipio).label("biblioteca_municipio"),
            func.count(Ejemplar.id).label("ejemplares"),
        )
        .join(Biblioteca, Biblioteca.id == Ejemplar.biblioteca_id)
        .join(Fuente, Fuente.id == Biblioteca.fuente_id)
        .outerjoin(
            Sucursal,
            (Sucursal.codigo == Ejemplar.sucursal_codigo)
            & (Sucursal.fuente_id == Biblioteca.fuente_id),
        )
        .where(Ejemplar.sucursal_codigo.is_not(None))
        .group_by(
            Biblioteca.id,
            Fuente.codigo,
            Biblioteca.codigo,
            Biblioteca.nombre,
            Ejemplar.sucursal_codigo,
        )
    )

    locations = [
        LocationOut(
            fuente=row.fuente,
            codigo=f"b:{row.fuente}:{row.codigo}",
            nombre=row.nombre,
            tipo="biblioteca",
            biblioteca_codigo=row.codigo,
            biblioteca_nombre=row.nombre,
            municipio=row.municipio,
            ejemplares=int(row.ejemplares),
        )
        for row in session.execute(libraries_stmt)
    ]
    locations.extend(
        LocationOut(
            fuente=row.fuente,
            codigo=f"s:{row.fuente}:{row.sucursal_codigo}",
            nombre=row.sucursal_nombre or row.sucursal_codigo,
            tipo="sucursal",
            biblioteca_codigo=row.biblioteca_codigo,
            biblioteca_nombre=row.biblioteca_nombre,
            municipio=row.sucursal_municipio or row.biblioteca_municipio,
            ejemplares=int(row.ejemplares),
        )
        for row in session.execute(branches_stmt)
    )
    locations.sort(
        key=lambda location: (
            location.biblioteca_nombre.casefold(),
            0 if location.tipo == "biblioteca" else 1,
            location.nombre.casefold(),
        )
    )
    return locations


@router.get("/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_db)) -> StatsResponse:
    ediciones = session.scalars(select(Edicion)).all()
    por_soporte: Counter[str] = Counter()
    for edicion in ediciones:
        for soporte in edicion.soportes or []:
            por_soporte[soporte] += 1

    ejemplares = session.scalar(select(func.count(Ejemplar.id))) or 0
    bibliotecas = session.scalar(select(func.count(Biblioteca.id))) or 0

    return StatsResponse(
        ediciones=len(ediciones),
        ejemplares=ejemplares,
        bibliotecas=bibliotecas,
        por_soporte=dict(por_soporte.most_common()),
    )
