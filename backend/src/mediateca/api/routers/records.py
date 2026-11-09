from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from mediateca.api.deps import get_db
from mediateca.api.schemas import RecordDetail
from mediateca.api.serializers import serialize_record
from mediateca.catalog.models import (
    Edicion,
    EdicionMateria,
    EdicionPersona,
    Ejemplar,
)

router = APIRouter(tags=["registros"])


@router.get("/records/{titn}", response_model=RecordDetail)
def get_record(titn: str, session: Session = Depends(get_db)) -> RecordDetail:
    stmt = (
        select(Edicion)
        .where(Edicion.titn == titn)
        .options(
            joinedload(Edicion.obra),
            selectinload(Edicion.ejemplares).selectinload(Ejemplar.biblioteca),
            selectinload(Edicion.personas).selectinload(EdicionPersona.persona),
            selectinload(Edicion.materias).selectinload(EdicionMateria.materia),
            selectinload(Edicion.enlaces),
        )
    )
    edicion = session.scalars(stmt).first()
    if edicion is None:
        raise HTTPException(status_code=404, detail=f"No existe el registro {titn}")
    return RecordDetail(**serialize_record(edicion))
