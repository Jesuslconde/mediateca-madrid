from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from mediateca_shared.models import Edicion, Obra
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC)


def _obra_key_query(titulo_uniforme: str, anio: int | None):
    stmt = select(Obra).where(Obra.titulo_uniforme == titulo_uniforme)
    if anio is None:
        stmt = stmt.where(Obra.anio.is_(None))
    else:
        stmt = stmt.where(Obra.anio == anio)
    return stmt


def find_or_create_obra(
    session: Session,
    titulo_uniforme: str,
    anio: int | None,
    *,
    director_principal: str | None = None,
    manual: bool = False,
) -> Obra:
    titulo = titulo_uniforme.strip()
    if not titulo:
        raise ValueError("El titulo uniforme no puede estar vacio")

    with session.no_autoflush:
        obra = session.scalars(_obra_key_query(titulo, anio)).first()
        if obra is None:
            obra = Obra(
                titulo_uniforme=titulo,
                anio=anio,
                director_principal=director_principal,
                manual=manual,
            )
            session.add(obra)
            session.flush()
        elif obra.director_principal is None and director_principal is not None:
            obra.director_principal = director_principal
    return obra


def _refresh_obra_manual(session: Session, obra: Obra) -> None:
    manual_count = int(
        session.scalar(
            select(func.count(Edicion.id)).where(
                Edicion.obra_id == obra.id,
                Edicion.obra_manual.is_(True),
            )
        )
        or 0
    )
    obra.manual = manual_count > 0


def _reconcile_obra(session: Session, obra_id: int) -> None:
    count = int(
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.obra_id == obra_id)
        )
        or 0
    )
    if count == 0:
        obra = session.get(Obra, obra_id)
        if obra is not None:
            session.delete(obra)
        return
    obra = session.get(Obra, obra_id)
    if obra is not None:
        _refresh_obra_manual(session, obra)


def _unique_ediciones(ediciones: Iterable[Edicion]) -> list[Edicion]:
    result: list[Edicion] = []
    seen: set[int] = set()
    for edicion in ediciones:
        identity = edicion.id if edicion.id is not None else id(edicion)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(edicion)
    return result


def group_editions_into_obra(
    session: Session,
    ediciones: Iterable[Edicion],
    obra: Obra,
) -> list[str]:
    """Mueve las ediciones a la obra y las marca como agrupadas manualmente."""
    selected = _unique_ediciones(ediciones)
    if not selected:
        raise ValueError("No hay ediciones seleccionadas")

    timestamp = _now()
    previous_obra_ids = {
        edicion.obra_id
        for edicion in selected
        if edicion.obra_id is not None and edicion.obra_id != obra.id
    }

    for edicion in selected:
        edicion.obra = obra
        edicion.obra_manual = True
        edicion.obra_manual_at = timestamp
    session.flush()

    for edicion in session.scalars(
        select(Edicion).where(Edicion.obra_id == obra.id)
    ):
        if not edicion.obra_manual:
            edicion.obra_manual = True
            edicion.obra_manual_at = timestamp
    obra.manual = True
    session.flush()

    for obra_id in previous_obra_ids:
        _reconcile_obra(session, obra_id)
    session.flush()

    return [edicion.record_id for edicion in selected]


def create_obra_and_group(
    session: Session,
    ediciones: Iterable[Edicion],
    titulo_uniforme: str,
    anio: int | None,
) -> tuple[Obra, list[str]]:
    """Reutiliza la obra con la misma clave o crea una manual y agrupa."""
    obra = find_or_create_obra(session, titulo_uniforme, anio)
    affected = group_editions_into_obra(session, ediciones, obra)
    return obra, affected


def ungroup_edition(session: Session, edicion: Edicion) -> str:
    """Devuelve una edicion al comportamiento automatico por titulo y anio."""
    previous_obra_id = edicion.obra_id
    edicion.obra_manual = False
    edicion.obra_manual_at = None

    titulo = edicion.titulo_uniforme or edicion.titulo
    automatica = find_or_create_obra(session, titulo, edicion.anio)
    edicion.obra = automatica
    session.flush()

    if previous_obra_id is not None and previous_obra_id != automatica.id:
        _reconcile_obra(session, previous_obra_id)
    elif previous_obra_id is not None:
        _refresh_obra_manual(session, automatica)
    session.flush()

    return edicion.record_id
