from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca_shared.db import Base
from mediateca_shared.lists import Lista, ListaItem


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _lista(**overrides) -> Lista:
    values = {
        "id": uuid.uuid4(),
        "token_hash": "a" * 64,
        "expires_at": datetime.now(UTC) + timedelta(days=180),
    }
    values.update(overrides)
    return Lista(**values)


def test_tablas_de_listas_en_metadata() -> None:
    assert {"listas", "lista_items"} <= set(Base.metadata.tables)


def test_lista_usa_titulo_por_defecto() -> None:
    session = _session()
    lista = _lista()
    session.add(lista)
    session.commit()

    assert lista.titulo == "Mi lista"
    assert lista.created_at is not None


def test_lista_item_tiene_clave_compuesta() -> None:
    columnas = [columna.name for columna in ListaItem.__table__.primary_key.columns]
    assert columnas == ["lista_id", "record_id"]


def test_borrar_lista_elimina_sus_items() -> None:
    session = _session()
    lista = _lista()
    lista.items = [
        ListaItem(record_id="madrid:111", titulo_snapshot="Primera"),
        ListaItem(record_id="madrid:222", titulo_snapshot="Segunda"),
    ]
    session.add(lista)
    session.commit()

    session.delete(lista)
    session.commit()

    assert session.scalars(select(ListaItem)).all() == []
