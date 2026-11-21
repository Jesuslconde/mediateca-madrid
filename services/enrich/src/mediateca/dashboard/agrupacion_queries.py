from __future__ import annotations

from dataclasses import dataclass

from mediateca_shared.models import Edicion, Fuente, Obra
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

ESTADOS_AGRUPACION = ("sin_obra", "manual", "automatica")


@dataclass(slots=True)
class AgrupacionFilter:
    texto: str | None = None
    fuente: str | None = None
    soporte: str | None = None
    estado: str | None = None
    page: int = 1
    limit: int = DEFAULT_LIMIT


@dataclass(slots=True)
class AgrupacionSummary:
    total: int
    sin_obra: int
    manual: int
    automatica: int


def _predicates(filtro: AgrupacionFilter) -> list:
    clauses = []
    if filtro.texto:
        term = f"%{filtro.texto}%"
        clauses.append(or_(Edicion.titn.ilike(term), Edicion.titulo.ilike(term)))
    if filtro.fuente:
        clauses.append(
            Edicion.fuente_id
            == select(Fuente.id).where(Fuente.codigo == filtro.fuente).scalar_subquery()
        )
    if filtro.soporte:
        clauses.append(Edicion.soporte_principal == filtro.soporte)
    if filtro.estado == "sin_obra":
        clauses.append(Edicion.obra_id.is_(None))
    elif filtro.estado == "manual":
        clauses.append(Edicion.obra_manual.is_(True))
    elif filtro.estado == "automatica":
        clauses.append(Edicion.obra_id.is_not(None))
        clauses.append(Edicion.obra_manual.is_(False))
    return clauses


def agrupacion_total(session: Session, filtro: AgrupacionFilter) -> int:
    total = session.scalar(
        select(func.count(Edicion.id)).where(*_predicates(filtro))
    )
    return int(total or 0)


def agrupacion_rows(session: Session, filtro: AgrupacionFilter) -> list[Edicion]:
    limit = min(max(filtro.limit, 1), MAX_LIMIT)
    page = max(filtro.page, 1)
    offset = (page - 1) * limit
    stmt = (
        select(Edicion)
        .where(*_predicates(filtro))
        .order_by(Edicion.record_id)
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(stmt))


def agrupacion_summary(session: Session) -> AgrupacionSummary:
    total = int(session.scalar(select(func.count(Edicion.id))) or 0)
    sin_obra = int(
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.obra_id.is_(None))
        )
        or 0
    )
    manual = int(
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.obra_manual.is_(True))
        )
        or 0
    )
    automatica = int(
        session.scalar(
            select(func.count(Edicion.id)).where(
                Edicion.obra_id.is_not(None),
                Edicion.obra_manual.is_(False),
            )
        )
        or 0
    )
    return AgrupacionSummary(
        total=total, sin_obra=sin_obra, manual=manual, automatica=automatica
    )


def obras_candidatas(session: Session) -> list[Obra]:
    stmt = select(Obra).order_by(Obra.titulo_uniforme, Obra.anio)
    return list(session.scalars(stmt))
