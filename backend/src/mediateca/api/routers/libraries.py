from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from mediateca.api.deps import get_db
from mediateca.api.schemas import LibraryOut, StatsResponse
from mediateca.catalog.models import Biblioteca, Edicion, Ejemplar

router = APIRouter(tags=["bibliotecas"])


@router.get("/libraries", response_model=list[LibraryOut])
def list_libraries(session: Session = Depends(get_db)) -> list[LibraryOut]:
    stmt = (
        select(
            Biblioteca.codigo,
            Biblioteca.nombre,
            Biblioteca.municipio,
            func.count(Ejemplar.id).label("ejemplares"),
            func.coalesce(
                func.sum(case((Ejemplar.disponible.is_(True), 1), else_=0)), 0
            ).label("disponibles"),
        )
        .outerjoin(Ejemplar, Ejemplar.biblioteca_id == Biblioteca.id)
        .group_by(Biblioteca.id)
        .order_by(Biblioteca.nombre)
    )
    return [
        LibraryOut(
            codigo=row.codigo,
            nombre=row.nombre,
            municipio=row.municipio,
            ejemplares=row.ejemplares,
            disponibles=int(row.disponibles or 0),
        )
        for row in session.execute(stmt)
    ]


@router.get("/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_db)) -> StatsResponse:
    ediciones = session.scalars(select(Edicion)).all()
    por_soporte: Counter[str] = Counter()
    for edicion in ediciones:
        for soporte in edicion.soportes or []:
            por_soporte[soporte] += 1

    ejemplares = session.scalar(select(func.count(Ejemplar.id))) or 0
    disponibles = (
        session.scalar(
            select(func.count(Ejemplar.id)).where(Ejemplar.disponible.is_(True))
        )
        or 0
    )
    bibliotecas = session.scalar(select(func.count(Biblioteca.id))) or 0

    return StatsResponse(
        ediciones=len(ediciones),
        ejemplares=ejemplares,
        disponibles=disponibles,
        bibliotecas=bibliotecas,
        por_soporte=dict(por_soporte.most_common()),
    )
