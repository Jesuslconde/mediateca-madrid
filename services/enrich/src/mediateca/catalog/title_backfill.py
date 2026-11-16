from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mediateca_shared.models import Edicion
from mediateca_shared.titles import clean_title, split_responsibility
from sqlalchemy import select
from sqlalchemy.orm import Session

SAMPLE_LIMIT = 10


@dataclass(slots=True)
class TitleChange:
    titn: str
    old_titulo: str | None
    new_titulo: str | None
    old_titulo_uniforme: str | None
    new_titulo_uniforme: str | None


@dataclass(slots=True)
class BackfillStats:
    scanned: int = 0
    changed: int = 0
    unchanged: int = 0
    samples: list[TitleChange] = field(default_factory=list)
    changed_titns: list[str] = field(default_factory=list)


def _first(value: Any) -> str | None:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def title_from_marc(marc: dict[str, Any], fallback: str | None) -> str | None:
    """Calcula el título propio desde el MARC guardado, sin volver a scrapear."""
    candidates = [
        _first(marc.get("T245ab")),
        _first(marc.get("T245a")),
        split_responsibility(_first(marc.get("T245"))),
        _first(marc.get("ntitl")),
        fallback,
    ]
    for candidate in candidates:
        cleaned = clean_title(candidate)
        if cleaned:
            return cleaned
    return None


def backfill_titles(
    session: Session,
    *,
    apply: bool = False,
    limit: int | None = None,
) -> BackfillStats:
    """Recalcula títulos existentes. Sin ``apply`` solo informa de los cambios."""
    stmt = select(Edicion).order_by(Edicion.titn)
    if limit is not None:
        stmt = stmt.limit(limit)

    stats = BackfillStats()
    for edicion in session.scalars(stmt):
        stats.scanned += 1
        new_titulo = title_from_marc(edicion.marc or {}, edicion.titulo) or edicion.titulo
        new_titulo_uniforme = clean_title(edicion.titulo_uniforme)

        titulo_changed = new_titulo != edicion.titulo
        uniforme_changed = new_titulo_uniforme != edicion.titulo_uniforme
        if not titulo_changed and not uniforme_changed:
            stats.unchanged += 1
            continue

        stats.changed += 1
        stats.changed_titns.append(edicion.titn)
        if len(stats.samples) < SAMPLE_LIMIT:
            stats.samples.append(
                TitleChange(
                    titn=edicion.titn,
                    old_titulo=edicion.titulo,
                    new_titulo=new_titulo,
                    old_titulo_uniforme=edicion.titulo_uniforme,
                    new_titulo_uniforme=new_titulo_uniforme,
                )
            )

        if apply:
            edicion.titulo = new_titulo
            edicion.titulo_uniforme = new_titulo_uniforme

    return stats
