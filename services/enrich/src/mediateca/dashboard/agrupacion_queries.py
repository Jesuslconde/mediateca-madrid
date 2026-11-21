from __future__ import annotations

from dataclasses import dataclass

from mediateca_shared.models import Edicion, Fuente, Obra
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import Session

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
MAX_CANDIDATES = 20


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


@dataclass(slots=True)
class ObraCandidata:
    obra: Obra
    ediciones_count: int


def _base_predicates(filtro: AgrupacionFilter) -> list:
    clauses = []
    if filtro.texto:
        term = f"%{filtro.texto}%"
        clauses.append(
            or_(
                Edicion.titn.ilike(term),
                Edicion.titulo.ilike(term),
                Edicion.titulo_uniforme.ilike(term),
                Obra.titulo_uniforme.ilike(term),
            )
        )
    if filtro.fuente:
        clauses.append(
            Edicion.fuente_id
            == select(Fuente.id).where(Fuente.codigo == filtro.fuente).scalar_subquery()
        )
    if filtro.soporte:
        clauses.append(Edicion.soporte_principal == filtro.soporte)
    return clauses


def _state_predicate(estado: str | None):
    if estado == "sin_obra":
        return Edicion.obra_id.is_(None)
    if estado == "manual":
        return Edicion.obra_manual.is_(True)
    if estado == "automatica":
        return and_(Edicion.obra_id.is_not(None), Edicion.obra_manual.is_(False))
    return None


def _predicates(filtro: AgrupacionFilter) -> list:
    clauses = _base_predicates(filtro)
    state = _state_predicate(filtro.estado)
    if state is not None:
        clauses.append(state)
    return clauses


def _select_ediciones(filtro: AgrupacionFilter):
    return (
        select(Edicion)
        .outerjoin(Obra, Edicion.obra_id == Obra.id)
        .where(*_predicates(filtro))
    )


def agrupacion_total(session: Session, filtro: AgrupacionFilter) -> int:
    total = session.scalar(
        select(func.count(Edicion.id))
        .outerjoin(Obra, Edicion.obra_id == Obra.id)
        .where(*_predicates(filtro))
    )
    return int(total or 0)


def agrupacion_rows(session: Session, filtro: AgrupacionFilter) -> list[Edicion]:
    limit = min(max(filtro.limit, 1), MAX_LIMIT)
    page = max(filtro.page, 1)
    offset = (page - 1) * limit
    stmt = (
        _select_ediciones(filtro)
        .order_by(Edicion.record_id)
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(stmt))


def agrupacion_summary(
    session: Session, filtro: AgrupacionFilter
) -> AgrupacionSummary:
    base = AgrupacionFilter(
        texto=filtro.texto,
        fuente=filtro.fuente,
        soporte=filtro.soporte,
        page=filtro.page,
        limit=filtro.limit,
    )
    clauses = _base_predicates(base)
    join = select(func.count(Edicion.id)).outerjoin(
        Obra, Edicion.obra_id == Obra.id
    )

    def count_with(*extra) -> int:
        return int(session.scalar(join.where(*clauses, *extra)) or 0)

    sin_obra = count_with(Edicion.obra_id.is_(None))
    manual = count_with(Edicion.obra_manual.is_(True))
    automatica = count_with(
        Edicion.obra_id.is_not(None), Edicion.obra_manual.is_(False)
    )
    return AgrupacionSummary(
        total=count_with(),
        sin_obra=sin_obra,
        manual=manual,
        automatica=automatica,
    )


def obra_candidates(
    session: Session, texto: str | None, *, limit: int = MAX_CANDIDATES
) -> list[ObraCandidata]:
    term_text = (texto or "").strip()
    if not term_text:
        return []
    term = f"%{term_text}%"
    limit = min(max(limit, 1), MAX_CANDIDATES)
    stmt = (
        select(Obra, func.count(Edicion.id).label("ediciones_count"))
        .outerjoin(Edicion, Edicion.obra_id == Obra.id)
        .where(
            or_(
                Obra.titulo_uniforme.ilike(term),
                cast(Obra.anio, String).ilike(term),
            )
        )
        .group_by(Obra.id)
        .order_by(Obra.titulo_uniforme, Obra.anio)
        .limit(limit)
    )
    return [
        ObraCandidata(obra=obra, ediciones_count=int(count))
        for obra, count in session.execute(stmt).all()
    ]
