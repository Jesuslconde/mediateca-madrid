from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from mediateca_shared.db import Base
from mediateca_shared.lists import Lista, ListaItem
from mediateca_shared.models import Edicion, Fuente
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.api.deps import get_db
from mediateca.api.main import app
from mediateca.core.logging import TokenMaskFilter


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    fuente = Fuente(codigo="madrid", nombre="Madrid", base_url="https://opac.example")
    session.add(fuente)
    session.commit()
    session.info["fuente"] = fuente
    return session


def _request(session: Session, method: str, url: str, **kwargs):
    app.dependency_overrides[get_db] = lambda: session
    try:
        return getattr(TestClient(app), method)(url, **kwargs)
    finally:
        app.dependency_overrides.clear()


def _crear_lista(session: Session, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    headers.setdefault("X-Client-IP", f"prueba-{uuid.uuid4()}")
    response = _request(session, "post", "/api/lists", headers=headers, **kwargs)
    assert response.status_code == 201
    return response.json()["token"]


def _edicion(session: Session, titn: str, titulo: str, **kwargs) -> Edicion:
    return Edicion(
        fuente_id=session.info["fuente"].id,
        record_id=f"madrid:{titn}",
        titn=titn,
        titulo=titulo,
        **kwargs,
    )


def test_crear_y_consultar_lista() -> None:
    session = _session()
    response = _request(
        session,
        "post",
        "/api/lists",
        headers={"X-Client-IP": f"prueba-{uuid.uuid4()}"},
    )

    assert response.status_code == 201
    token = response.json()["token"]
    assert len(token) >= 32

    lista = session.scalars(select(Lista)).one()
    assert lista.token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token not in lista.token_hash

    response = _request(session, "get", f"/api/lists/{token}")
    assert response.status_code == 200
    body = response.json()
    assert body["titulo"] == "Mi lista"
    assert body["item_count"] == 0
    assert body["items"] == []


def test_anadir_es_idempotente_y_quitar() -> None:
    session = _session()
    session.add(_edicion(session, "111", "Primera", soportes=["DVD"], anio=2001))
    session.commit()
    token = _crear_lista(session)

    response = _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})
    assert response.status_code == 201
    assert response.json() == {"item_count": 1, "saved": True}

    response = _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})
    assert response.status_code == 200
    assert response.json() == {"item_count": 1, "saved": True}

    response = _request(session, "delete", f"/api/lists/{token}/items/111")
    assert response.status_code == 200
    assert response.json() == {"item_count": 0, "saved": False}


def test_elementos_del_mas_reciente_al_mas_antiguo() -> None:
    session = _session()
    session.add_all([_edicion(session, "111", "Primera"), _edicion(session, "222", "Segunda")])
    session.commit()
    token = _crear_lista(session)

    _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})
    time.sleep(0.002)
    _request(session, "post", f"/api/lists/{token}/items", json={"titn": "222"})

    body = _request(session, "get", f"/api/lists/{token}").json()
    assert [item["titn"] for item in body["items"]] == ["222", "111"]


def test_edicion_inexistente() -> None:
    session = _session()
    token = _crear_lista(session)

    response = _request(session, "post", f"/api/lists/{token}/items", json={"titn": "999"})
    assert response.status_code == 422
    assert "999" in response.json()["detail"]

    body = _request(session, "get", f"/api/lists/{token}").json()
    assert body["item_count"] == 0


def test_ficha_desaparecida_conserva_titulo() -> None:
    session = _session()
    edicion = _edicion(session, "111", "Titulo guardado")
    session.add(edicion)
    session.commit()
    token = _crear_lista(session)
    _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})

    session.delete(edicion)
    session.commit()

    body = _request(session, "get", f"/api/lists/{token}").json()
    item = body["items"][0]
    assert item["titulo"] == "Titulo guardado"
    assert item["disponible"] is False
    assert item["opac_url"] is None


def test_token_invalido() -> None:
    session = _session()
    assert _request(session, "get", "/api/lists/no-existe").status_code == 404
    assert _request(session, "post", "/api/lists/no-existe/items", json={"titn": "1"}).status_code == 404


def test_mutacion_renueva_fechas() -> None:
    session = _session()
    session.add(_edicion(session, "111", "Primera"))
    session.commit()
    token = _crear_lista(session)
    lista = session.scalars(select(Lista)).one()
    original = lista.expires_at

    time.sleep(0.002)
    _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})
    session.refresh(lista)

    assert lista.expires_at > original


def test_lista_llena() -> None:
    session = _session()
    session.add(_edicion(session, "111", "Primera"))
    session.commit()
    token = _crear_lista(session)
    lista = session.scalars(select(Lista)).one()
    for index in range(200):
        session.add(
            ListaItem(
                lista_id=lista.id,
                record_id=f"madrid:relleno-{index}",
                titulo_snapshot="Relleno",
                added_at=datetime.now(UTC),
            )
        )
    session.commit()

    response = _request(session, "post", f"/api/lists/{token}/items", json={"titn": "111"})
    assert response.status_code == 409
    assert "200" in response.json()["detail"]


def test_renombrar_lista() -> None:
    session = _session()
    token = _crear_lista(session)

    body = _request(
        session, "patch", f"/api/lists/{token}", json={"titulo": "  Mi seleccion  "}
    ).json()
    assert body["titulo"] == "Mi seleccion"

    body = _request(session, "patch", f"/api/lists/{token}", json={"titulo": ""}).json()
    assert body["titulo"] == "Mi lista"

    body = _request(
        session, "patch", f"/api/lists/{token}", json={"titulo": "x" * 120}
    ).json()
    assert len(body["titulo"]) == 80


def test_limite_de_creacion() -> None:
    session = _session()
    ip = f"prueba-{uuid.uuid4()}"

    for _ in range(5):
        assert _request(session, "post", "/api/lists", headers={"X-Client-IP": ip}).status_code == 201

    response = _request(session, "post", "/api/lists", headers={"X-Client-IP": ip})
    assert response.status_code == 429


def test_filtro_de_logs_enmascara_token() -> None:
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1", "GET", "/api/lists/token-secreto", "1.1", 200),
        None,
    )

    TokenMaskFilter().filter(record)

    assert "token-secreto" not in record.getMessage()
    assert "/api/lists/***" in record.getMessage()
