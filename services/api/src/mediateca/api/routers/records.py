from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from mediateca_shared.identity import RecordIdError, normalize_record_id
from mediateca_shared.models import (
    Edicion,
    EdicionMateria,
    EdicionPersona,
    Ejemplar,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from mediateca.api.deps import get_db
from mediateca.api.schemas import RecordDetail
from mediateca.api.serializers import serialize_record

router = APIRouter(tags=["registros"])


@router.get("/records/{record_id}", response_model=RecordDetail)
def get_record(record_id: str, session: Session = Depends(get_db)) -> RecordDetail:
    try:
        normalized = normalize_record_id(record_id)
    except RecordIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    stmt = (
        select(Edicion)
        .where(Edicion.record_id == normalized)
        .options(
            joinedload(Edicion.fuente),
            joinedload(Edicion.obra),
            selectinload(Edicion.ejemplares).selectinload(Ejemplar.biblioteca),
            selectinload(Edicion.ejemplares).selectinload(Ejemplar.sucursal),
            selectinload(Edicion.personas).selectinload(EdicionPersona.persona),
            selectinload(Edicion.materias).selectinload(EdicionMateria.materia),
            selectinload(Edicion.enlaces),
        )
    )
    edicion = session.scalars(stmt).first()
    if edicion is None:
        raise HTTPException(status_code=404, detail=f"No existe el registro {record_id}")
    return RecordDetail(**serialize_record(edicion))
