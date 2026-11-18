from __future__ import annotations

from dataclasses import dataclass

from mediateca_shared.constants import ENRICH_STATUSES, TMDB_STATUSES
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(slots=True)
class CatalogFilter:
    enrich_status: str | None = None
    tmdb_status: str | None = None
    missing: str = "incluir"
    texto: str | None = None
    soporte: str | None = None
    biblioteca: str | None = None
    anio_desde: int | None = None
    anio_hasta: int | None = None
    idioma: str | None = None
    pais: str | None = None
    fuente: str | None = None
    page: int = 1
    limit: int = DEFAULT_LIMIT


@dataclass(slots=True)
class CatalogSummary:
    total: int
    por_enrich: dict[str, int]
    por_tmdb: dict[str, int]
    desaparecidas: int


def _predicates(filtro: CatalogFilter) -> list:
    clauses = []
    if filtro.enrich_status:
        clauses.append(Edicion.enrich_status == filtro.enrich_status)
    if filtro.tmdb_status:
        clauses.append(Edicion.tmdb_status == filtro.tmdb_status)
    if filtro.missing == "excluir":
        clauses.append(Edicion.missing_at.is_(None))
    elif filtro.missing == "solo":
        clauses.append(Edicion.missing_at.is_not(None))
    if filtro.texto:
        term = f"%{filtro.texto}%"
        clauses.append(or_(Edicion.titn.ilike(term), Edicion.titulo.ilike(term)))
    if filtro.soporte:
        clauses.append(Edicion.soporte_principal == filtro.soporte)
    if filtro.biblioteca:
        clauses.append(
            exists(
                select(1)
                .select_from(Ejemplar)
                .join(Biblioteca, Ejemplar.biblioteca_id == Biblioteca.id)
                .where(
                    Ejemplar.edicion_id == Edicion.id,
                    Biblioteca.codigo == filtro.biblioteca,
                )
            )
        )
    if filtro.anio_desde is not None:
        clauses.append(Edicion.anio >= filtro.anio_desde)
    if filtro.anio_hasta is not None:
        clauses.append(Edicion.anio <= filtro.anio_hasta)
    if filtro.idioma:
        clauses.append(Edicion.idioma == filtro.idioma)
    if filtro.pais:
        clauses.append(Edicion.pais == filtro.pais)
    if filtro.fuente:
        clauses.append(
            Edicion.fuente_id
            == select(Fuente.id).where(Fuente.codigo == filtro.fuente).scalar_subquery()
        )
    return clauses


def catalog_total(session: Session, filtro: CatalogFilter) -> int:
    total = session.scalar(
        select(func.count(Edicion.id)).where(*_predicates(filtro))
    )
    return int(total or 0)


def catalog_rows(session: Session, filtro: CatalogFilter) -> list[Edicion]:
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


def catalog_summary(session: Session, filtro: CatalogFilter) -> CatalogSummary:
    predicates = _predicates(filtro)
    total = int(
        session.scalar(select(func.count(Edicion.id)).where(*predicates)) or 0
    )
    por_enrich = {status: 0 for status in ENRICH_STATUSES}
    for status, count in session.execute(
        select(Edicion.enrich_status, func.count(Edicion.id))
        .where(*predicates)
        .group_by(Edicion.enrich_status)
    ).all():
        por_enrich[str(status)] = int(count)

    por_tmdb = {status: 0 for status in TMDB_STATUSES}
    for status, count in session.execute(
        select(Edicion.tmdb_status, func.count(Edicion.id))
        .where(*predicates)
        .group_by(Edicion.tmdb_status)
    ).all():
        por_tmdb[str(status)] = int(count)

    desaparecidas = int(
        session.scalar(
            select(func.count(Edicion.id)).where(
                *predicates, Edicion.missing_at.is_not(None)
            )
        )
        or 0
    )
    return CatalogSummary(
        total=total,
        por_enrich=por_enrich,
        por_tmdb=por_tmdb,
        desaparecidas=desaparecidas,
    )
