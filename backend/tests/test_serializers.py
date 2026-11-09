from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.api.serializers import serialize_record
from mediateca.catalog.parser import parse_file
from mediateca.catalog.repository import upsert_edicion
from mediateca.core.db import Base


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_serialize_record_sin_disponibilidad(dvd_fixture) -> None:
    session = _session()
    edicion = upsert_edicion(session, parse_file(str(dvd_fixture)))
    session.commit()

    data = serialize_record(edicion)

    assert "disponible" not in data
    assert data["source_url"]
    assert len(data["ejemplares"]) == 2
    for ejemplar in data["ejemplares"]:
        assert "disponible" not in ejemplar
        assert "estado" not in ejemplar
        assert ejemplar["biblioteca"]
        assert ejemplar["soporte"] == "DVD"
