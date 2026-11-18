from __future__ import annotations

import hashlib
import secrets
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from threading import Lock

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from mediateca_shared.fuentes import MADRID_PROFILE, FuenteProfile
from mediateca_shared.identity import normalize_record_id, parse_record_id
from mediateca_shared.lists import Lista, ListaItem
from mediateca_shared.models import Edicion
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from mediateca.api.deps import get_db
from mediateca.api.schemas import (
    ItemMutationOut,
    ListaCreatedOut,
    ListaItemIn,
    ListaItemOut,
    ListaOut,
    ListaRenameIn,
)

router = APIRouter(tags=["listas"])

TTL_DIAS = 180
MAX_ITEMS = 200
RATE_LIMIT_CREACION = 5
GLOBAL_RATE_LIMIT_CREACION = 60
RATE_WINDOW = timedelta(hours=1)
TITULO_POR_DEFECTO = "Mi lista"

_creations: dict[str, deque[datetime]] = defaultdict(deque)
_rate_lock = Lock()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _expired(value: datetime) -> bool:
    now = datetime.now(UTC)
    if value.tzinfo is None:
        return value <= now.replace(tzinfo=None)
    return value <= now


def _touch(lista: Lista) -> None:
    now = datetime.now(UTC)
    lista.updated_at = now
    lista.expires_at = now + timedelta(days=TTL_DIAS)


def _normalize_title(value: str | None) -> str:
    title = (value or "").strip()
    return title[:80] if title else TITULO_POR_DEFECTO


def _opac_url(edicion: Edicion) -> str:
    profile = (
        FuenteProfile.from_model(edicion.fuente)
        if edicion.fuente is not None
        else MADRID_PROFILE
    )
    return profile.source_url(edicion.titn)


def _client_key(request: Request, x_client_ip: str | None) -> str:
    value = (x_client_ip or "").strip()
    if not value:
        forwarded = request.headers.get("x-forwarded-for", "")
        value = forwarded.split(",")[0].strip()
    return value or "global"


def _enforce_creation_limit(key: str) -> None:
    limit = GLOBAL_RATE_LIMIT_CREACION if key == "global" else RATE_LIMIT_CREACION
    now = datetime.now(UTC)
    with _rate_lock:
        bucket = _creations[key]
        while bucket and now - bucket[0] > RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas listas creadas. Intentalo mas tarde.",
            )
        bucket.append(now)


def _get_lista(session: Session, token: str) -> Lista:
    lista = session.scalar(select(Lista).where(Lista.token_hash == _hash_token(token)))
    if lista is None or _expired(lista.expires_at):
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    return lista


def _item_count(session: Session, lista_id: uuid.UUID) -> int:
    return (
        session.scalar(
            select(func.count()).select_from(ListaItem).where(ListaItem.lista_id == lista_id)
        )
        or 0
    )


def _serialize_items(session: Session, lista: Lista) -> list[ListaItemOut]:
    items = session.scalars(
        select(ListaItem)
        .where(ListaItem.lista_id == lista.id)
        .order_by(ListaItem.added_at.desc(), ListaItem.record_id)
    ).all()
    record_ids = [item.record_id for item in items]
    ediciones: dict[str, Edicion] = {}
    if record_ids:
        ediciones = {
            edicion.record_id: edicion
            for edicion in session.scalars(
                select(Edicion)
                .where(Edicion.record_id.in_(record_ids))
                .options(joinedload(Edicion.fuente))
            ).all()
        }

    payload: list[ListaItemOut] = []
    for item in items:
        fuente, titn = parse_record_id(item.record_id)
        edicion = ediciones.get(item.record_id)
        if edicion is None:
            payload.append(
                ListaItemOut(
                    record_id=item.record_id,
                    fuente=fuente,
                    titn=titn,
                    titulo=item.titulo_snapshot,
                    disponible=False,
                )
            )
            continue
        disponible = edicion.missing_at is None
        payload.append(
            ListaItemOut(
                record_id=edicion.record_id,
                fuente=fuente,
                titn=edicion.titn,
                titulo=edicion.titulo,
                soportes=edicion.soportes or [],
                anio=edicion.anio,
                poster_url=edicion.tmdb_poster_url,
                opac_url=_opac_url(edicion) if disponible else None,
                disponible=disponible,
            )
        )
    return payload


def _lista_out(session: Session, lista: Lista) -> ListaOut:
    items = _serialize_items(session, lista)
    return ListaOut(
        titulo=lista.titulo or TITULO_POR_DEFECTO,
        item_count=len(items),
        created_at=lista.created_at,
        updated_at=lista.updated_at,
        expires_at=lista.expires_at,
        items=items,
    )


@router.post("/lists", response_model=ListaCreatedOut, status_code=201)
def create_list(
    request: Request,
    x_client_ip: str | None = Header(default=None),
    session: Session = Depends(get_db),
) -> ListaCreatedOut:
    _enforce_creation_limit(_client_key(request, x_client_ip))
    token = secrets.token_urlsafe(24)
    now = datetime.now(UTC)
    lista = Lista(
        id=uuid.uuid4(),
        token_hash=_hash_token(token),
        titulo=TITULO_POR_DEFECTO,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(days=TTL_DIAS),
    )
    session.add(lista)
    session.commit()
    return ListaCreatedOut(token=token)


@router.get("/lists/{token}", response_model=ListaOut)
def get_list(token: str, session: Session = Depends(get_db)) -> ListaOut:
    return _lista_out(session, _get_lista(session, token))


@router.post("/lists/{token}/items", response_model=ItemMutationOut)
def add_item(
    token: str,
    payload: ListaItemIn,
    response: Response,
    session: Session = Depends(get_db),
) -> ItemMutationOut:
    lista = _get_lista(session, token)
    record_id = normalize_record_id(payload.identity)
    edicion = session.scalar(
        select(Edicion).where(Edicion.record_id == record_id)
    )
    if edicion is None:
        raise HTTPException(status_code=422, detail=f"No existe la edicion {record_id}")

    existing = session.get(ListaItem, (lista.id, record_id))
    if existing is not None:
        response.status_code = 200
        return ItemMutationOut(item_count=_item_count(session, lista.id), saved=True)

    if _item_count(session, lista.id) >= MAX_ITEMS:
        raise HTTPException(
            status_code=409,
            detail=f"La lista admite como maximo {MAX_ITEMS} elementos",
        )

    session.add(
        ListaItem(
            lista_id=lista.id,
            record_id=record_id,
            titulo_snapshot=edicion.titulo,
            added_at=datetime.now(UTC),
        )
    )
    _touch(lista)
    session.commit()
    response.status_code = 201
    return ItemMutationOut(item_count=_item_count(session, lista.id), saved=True)


@router.delete("/lists/{token}/items/{record_id}", response_model=ItemMutationOut)
def remove_item(
    token: str, record_id: str, session: Session = Depends(get_db)
) -> ItemMutationOut:
    lista = _get_lista(session, token)
    normalized = normalize_record_id(record_id)
    item = session.get(ListaItem, (lista.id, normalized))
    if item is not None:
        session.delete(item)
        _touch(lista)
        session.commit()
    return ItemMutationOut(item_count=_item_count(session, lista.id), saved=False)


@router.patch("/lists/{token}", response_model=ListaOut)
def rename_list(
    token: str,
    payload: ListaRenameIn,
    session: Session = Depends(get_db),
) -> ListaOut:
    lista = _get_lista(session, token)
    lista.titulo = _normalize_title(payload.titulo)
    _touch(lista)
    session.commit()
    return _lista_out(session, lista)
