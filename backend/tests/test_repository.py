from __future__ import annotations

from dataclasses import replace

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.models import (
    Biblioteca,
    Edicion,
    Ejemplar,
    HistorialDisponibilidad,
    Materia,
    Obra,
)
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


def test_upsert_es_idempotente_y_agrupa_obras(dvd_fixture, bluray_fixture) -> None:
    session = _session()
    dvd = parse_file(str(dvd_fixture))
    bluray = parse_file(str(bluray_fixture))

    upsert_edicion(session, dvd)
    upsert_edicion(session, dvd)
    session.commit()

    assert session.scalar(select(func.count(Edicion.id))) == 1
    assert session.scalar(select(func.count(Ejemplar.id))) == 2
    assert session.scalar(select(func.count(Biblioteca.id))) == 2
    assert session.scalar(select(func.count(Materia.id))) == 2
    assert session.scalar(select(func.count(HistorialDisponibilidad.id))) == 2

    upsert_edicion(session, bluray)
    session.commit()

    assert session.scalar(select(func.count(Edicion.id))) == 2
    assert session.scalar(select(func.count(Obra.id))) == 1
    assert session.scalar(select(func.count(Ejemplar.id))) == 3

    ediciones = session.scalars(select(Edicion)).all()
    soportes = sorted(soporte for edicion in ediciones for soporte in edicion.soportes)
    assert soportes == ["Blu-ray", "DVD"]


def test_reupsert_tras_commit_no_rompe_relaciones(dvd_fixture) -> None:
    session = _session()
    dvd = parse_file(str(dvd_fixture))

    upsert_edicion(session, dvd)
    session.commit()
    upsert_edicion(session, dvd)
    session.commit()

    assert session.scalar(select(func.count(Edicion.id))) == 1
    assert session.scalar(select(func.count(Ejemplar.id))) == 2
    assert session.scalar(select(func.count(Materia.id))) == 2


def test_deduplica_ejemplares_identicos(dvd_fixture) -> None:
    session = _session()
    dvd = parse_file(str(dvd_fixture))
    dvd.ejemplares.append(replace(dvd.ejemplares[0]))

    upsert_edicion(session, dvd)
    session.commit()

    assert session.scalar(select(func.count(Ejemplar.id))) == 2


def test_historial_solo_cambia_si_cambia_estado(dvd_fixture) -> None:
    session = _session()
    dvd = parse_file(str(dvd_fixture))

    upsert_edicion(session, dvd)
    session.commit()
    assert session.scalar(select(func.count(HistorialDisponibilidad.id))) == 2

    # El mismo estado no debe añadir historial nuevo.
    upsert_edicion(session, dvd)
    session.commit()
    assert session.scalar(select(func.count(HistorialDisponibilidad.id))) == 2

    # Un cambio de disponibilidad sí debe añadir una entrada.
    dvd.ejemplares[0].disponible = False
    dvd.ejemplares[0].estado = "Prestado"
    upsert_edicion(session, dvd)
    session.commit()
    assert session.scalar(select(func.count(HistorialDisponibilidad.id))) == 3
