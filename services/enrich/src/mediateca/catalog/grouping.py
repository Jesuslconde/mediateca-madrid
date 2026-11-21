from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from mediateca_shared.models import Edicion, Obra
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mediateca.catalog.repository import get_or_create_obra_by_key


def _now() -> datetime:
    return datetime.now(UTC)


def _cleanup_obra(session: Session, obra_id: int) -> None:
    """Desmarca una obra sin ediciones manuales o elimina una obra vacia."""
    obra = session.get(Obra, obra_id)
    if obra is None:
        return
    manual = (
        session.scalar(
            select(func.count(Edicion.id)).where(
                Edicion.obra_id == obra_id,
                Edicion.obra_manual.is_(True),
            )
        )
        or 0
    )
    total = (
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.obra_id == obra_id)
        )
        or 0
    )
    if total == 0:
        session.delete(obra)
    elif manual == 0:
        obra.manual = False
    session.flush()


def group_editions_into_obra(
    session: Session, ediciones: Iterable[Edicion], obra: Obra
) -> list[str]:
    """Asigna las ediciones a una obra existente y las marca como manuales.

    Elimina las obras antiguas que quedan sin ediciones y desmarca las que
    pierden todas sus ediciones manuales. Devuelve los ``record_id`` afectados.
    """
    now = _now()
    affected: set[str] = set()
    previous_ids: set[int] = set()
    for edicion in ediciones:
        if edicion.obra_id is not None and edicion.obra_id != obra.id:
            previous_ids.add(edicion.obra_id)
        edicion.obra = obra
        edicion.obra_manual = True
        edicion.obra_manual_at = now
        affected.add(edicion.record_id)
    obra.manual = True
    session.flush()
    for obra_id in previous_ids:
        _cleanup_obra(session, obra_id)
    session.flush()
    return sorted(affected)


def create_obra_and_group(
    session: Session,
    ediciones: Iterable[Edicion],
    *,
    titulo_uniforme: str,
    anio: int | None,
) -> list[str]:
    """Reutiliza la obra con la clave indicada (o la crea manual) y agrupa."""
    obra = get_or_create_obra_by_key(session, titulo_uniforme, anio)
    obra.manual = True
    return group_editions_into_obra(session, ediciones, obra)


def ungroup_edition(session: Session, edicion: Edicion) -> list[str]:
    """Devuelve una edicion al comportamiento automatico de agrupacion."""
    previous_id = edicion.obra_id
    titulo = edicion.titulo_uniforme or edicion.titulo
    obra = get_or_create_obra_by_key(session, titulo, edicion.anio)
    edicion.obra = obra
    edicion.obra_manual = False
    edicion.obra_manual_at = None
    session.flush()
    if previous_id is not None and previous_id != obra.id:
        _cleanup_obra(session, previous_id)
    session.flush()
    return [edicion.record_id]
