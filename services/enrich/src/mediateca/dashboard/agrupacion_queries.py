from __future__ import annotations

import time
from dataclasses import dataclass

from mediateca_shared.models import Edicion, Fuente, Obra
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import Session

from mediateca.core.logging import elapsed_ms, get_logger

logger = get_logger(__name__)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
MAX_CANDIDATES = 20


@dataclass(slots=True)
class AgrupacionFilter:
    texto: str | None = None
    fuente: str | None = None
    soporte: str | None = None
    estado: str | None = None
    anio: int | None = None
    amplio: bool = False
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
        # Por defecto la búsqueda es exacta; con ``amplio`` se busca por
        # coincidencia parcial (contiene) sobre los mismos campos.
        term = f"%{filtro.texto}%" if filtro.amplio else filtro.texto
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
    if filtro.anio is not None:
        clauses.append(Edicion.anio == filtro.anio)
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
    started = time.monotonic()
    logger.info(
        "Agrupacion total: consultando (q=%r, fuente=%r, soporte=%r, estado=%r, anio=%r, amplio=%r)",
        filtro.texto,
        filtro.fuente,
        filtro.soporte,
        filtro.estado,
        filtro.anio,
        filtro.amplio,
        extra={"step": "agrupacion.total.start"},
    )
    total = session.scalar(
        select(func.count(Edicion.id))
        .outerjoin(Obra, Edicion.obra_id == Obra.id)
        .where(*_predicates(filtro))
    )
    result = int(total or 0)
    logger.info(
        "Agrupacion total: %s ediciones en %.1f ms",
        result,
        elapsed_ms(started),
        extra={
            "step": "agrupacion.total.done",
            "duration_ms": elapsed_ms(started),
            "rows": result,
        },
    )
    return result


def agrupacion_rows(session: Session, filtro: AgrupacionFilter) -> list[Edicion]:
    limit = min(max(filtro.limit, 1), MAX_LIMIT)
    page = max(filtro.page, 1)
    offset = (page - 1) * limit
    started = time.monotonic()
    logger.info(
        "Agrupacion filas: consultando pagina=%s limit=%s offset=%s (q=%r, fuente=%r, soporte=%r, estado=%r, anio=%r, amplio=%r)",
        page,
        limit,
        offset,
        filtro.texto,
        filtro.fuente,
        filtro.soporte,
        filtro.estado,
        filtro.anio,
        filtro.amplio,
        extra={"step": "agrupacion.rows.start", "page": page},
    )
    stmt = (
        _select_ediciones(filtro)
        .order_by(Edicion.record_id)
        .limit(limit)
        .offset(offset)
    )
    rows = list(session.scalars(stmt))
    duration = elapsed_ms(started)
    logger.info(
        "Agrupacion filas: %s ediciones en %.1f ms%s",
        len(rows),
        duration,
        f" ({rows[0].record_id}..{rows[-1].record_id})" if rows else "",
        extra={
            "step": "agrupacion.rows.done",
            "duration_ms": duration,
            "rows": len(rows),
            "page": page,
        },
    )
    return rows


def agrupacion_summary(
    session: Session, filtro: AgrupacionFilter
) -> AgrupacionSummary:
    started = time.monotonic()
    base = AgrupacionFilter(
        texto=filtro.texto,
        fuente=filtro.fuente,
        soporte=filtro.soporte,
        anio=filtro.anio,
        amplio=filtro.amplio,
        page=filtro.page,
        limit=filtro.limit,
    )
    clauses = _base_predicates(base)
    join = select(func.count(Edicion.id)).outerjoin(
        Obra, Edicion.obra_id == Obra.id
    )
    logger.info(
        "Agrupacion resumen: consultando totales (q=%r, fuente=%r, soporte=%r, anio=%r, amplio=%r)",
        filtro.texto,
        filtro.fuente,
        filtro.soporte,
        filtro.anio,
        filtro.amplio,
        extra={"step": "agrupacion.summary.start"},
    )

    def count_with(name: str, *extra) -> int:
        count_started = time.monotonic()
        logger.info(
            "Agrupacion resumen: consulta %s iniciada",
            name,
            extra={"step": f"agrupacion.summary.{name}.start"},
        )
        value = int(session.scalar(join.where(*clauses, *extra)) or 0)
        logger.info(
            "Agrupacion resumen: consulta %s = %s en %.1f ms",
            name,
            value,
            elapsed_ms(count_started),
            extra={
                "step": f"agrupacion.summary.{name}.done",
                "duration_ms": elapsed_ms(count_started),
                "rows": value,
            },
        )
        return value

    sin_obra = count_with("sin_obra", Edicion.obra_id.is_(None))
    manual = count_with("manual", Edicion.obra_manual.is_(True))
    automatica = count_with(
        "automatica", Edicion.obra_id.is_not(None), Edicion.obra_manual.is_(False)
    )
    total = count_with("total")
    logger.info(
        "Agrupacion resumen: total=%s sin_obra=%s manual=%s automatica=%s en %.1f ms",
        total,
        sin_obra,
        manual,
        automatica,
        elapsed_ms(started),
        extra={
            "step": "agrupacion.summary.done",
            "duration_ms": elapsed_ms(started),
            "rows": total,
        },
    )
    return AgrupacionSummary(
        total=total,
        sin_obra=sin_obra,
        manual=manual,
        automatica=automatica,
    )


def obra_candidates(
    session: Session, texto: str | None, *, limit: int = MAX_CANDIDATES
) -> list[ObraCandidata]:
    term_text = (texto or "").strip()
    if not term_text:
        logger.info(
            "Agrupacion candidatas: sin texto, se omite la consulta",
            extra={"step": "agrupacion.candidates.skip"},
        )
        return []
    term = f"%{term_text}%"
    limit = min(max(limit, 1), MAX_CANDIDATES)
    started = time.monotonic()
    logger.info(
        "Agrupacion candidatas: buscando obras para %r (limit=%s)",
        term_text,
        limit,
        extra={"step": "agrupacion.candidates.start"},
    )
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
    candidates = [
        ObraCandidata(obra=obra, ediciones_count=int(count))
        for obra, count in session.execute(stmt).all()
    ]
    logger.info(
        "Agrupacion candidatas: %s obras para %r en %.1f ms",
        len(candidates),
        term_text,
        elapsed_ms(started),
        extra={
            "step": "agrupacion.candidates.done",
            "duration_ms": elapsed_ms(started),
            "rows": len(candidates),
        },
    )
    return candidates
