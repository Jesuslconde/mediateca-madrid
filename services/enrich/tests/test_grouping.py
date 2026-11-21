from __future__ import annotations

from mediateca_shared.models import Edicion, Fuente, Obra
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.grouping import (
    create_obra_and_group,
    group_editions_into_obra,
    ungroup_edition,
)
from mediateca.core.db import Base


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    fuente = Fuente(codigo="madrid", nombre="Madrid", base_url="https://opac.example")
    session.add(fuente)
    session.flush()
    session.info["fuente"] = fuente
    return session


def _obra(session, titulo_uniforme, anio, *, manual=False) -> Obra:
    obra = Obra(titulo_uniforme=titulo_uniforme, anio=anio)
    obra.manual = manual
    session.add(obra)
    session.flush()
    return obra


def _edicion(session, titn, *, obra=None, titulo_uniforme=None, anio=None) -> Edicion:
    edicion = Edicion(
        fuente_id=session.info["fuente"].id,
        record_id=f"madrid:{titn}",
        titn=titn,
        titulo=titulo_uniforme or f"Titulo {titn}",
        titulo_uniforme=titulo_uniforme,
        anio=anio,
        obra=obra,
    )
    session.add(edicion)
    session.flush()
    return edicion


def test_group_editions_into_existing_obra() -> None:
    session = _session()
    auto_a = _obra(session, "La vida padre", 2022)
    auto_b = _obra(session, "Otro titulo", 2020)
    dest = _obra(session, "La vida padre", 2023)
    e1 = _edicion(session, "1", obra=auto_a, titulo_uniforme="La vida padre", anio=2022)
    e2 = _edicion(session, "2", obra=auto_b, titulo_uniforme="Otro titulo", anio=2020)
    session.commit()

    affected = group_editions_into_obra(session, [e1, e2], dest)
    session.commit()

    assert set(affected) == {"madrid:1", "madrid:2"}
    assert e1.obra_id == dest.id
    assert e2.obra_id == dest.id
    assert e1.obra_manual is True
    assert e2.obra_manual is True
    assert e1.obra_manual_at is not None
    assert dest.manual is True
    # Las obras antiguas quedaron sin ediciones y se eliminaron.
    assert session.get(Obra, auto_a.id) is None
    assert session.get(Obra, auto_b.id) is None


def test_group_no_elimina_obra_con_ediciones_restantes() -> None:
    session = _session()
    auto_a = _obra(session, "La vida padre", 2022)
    dest = _obra(session, "La vida padre", 2023)
    e1 = _edicion(session, "1", obra=auto_a, titulo_uniforme="La vida padre", anio=2022)
    e2 = _edicion(session, "2", obra=auto_a, titulo_uniforme="La vida padre", anio=2022)
    session.commit()

    group_editions_into_obra(session, [e1], dest)
    session.commit()

    assert e1.obra_id == dest.id
    assert e2.obra_id == auto_a.id
    assert session.get(Obra, auto_a.id) is not None


def test_create_obra_and_group_reutiliza_existente() -> None:
    session = _session()
    existing = _obra(session, "La vida padre", 2022)
    e1 = _edicion(session, "1", titulo_uniforme="La vida padre", anio=2022)
    session.commit()

    create_obra_and_group(session, [e1], titulo_uniforme="La vida padre", anio=2022)
    session.commit()

    assert e1.obra_id == existing.id
    assert session.scalar(select(func.count(Obra.id))) == 1
    assert existing.manual is True


def test_create_obra_and_group_crea_obra_manual() -> None:
    session = _session()
    e1 = _edicion(session, "1", titulo_uniforme="La vida padre", anio=2022)
    session.commit()

    create_obra_and_group(session, [e1], titulo_uniforme="La vida padre", anio=2022)
    session.commit()

    obra = session.scalars(select(Obra)).one()
    assert obra.manual is True
    assert e1.obra_id == obra.id
    assert e1.obra_manual is True


def test_ungroup_recalcula_y_elimina_obra_vacia() -> None:
    session = _session()
    manual_obra = _obra(session, "La vida padre", 2023, manual=True)
    auto_obra = _obra(session, "La vida padre", 2022)
    e1 = _edicion(
        session,
        "1",
        obra=manual_obra,
        titulo_uniforme="La vida padre",
        anio=2022,
    )
    e1.obra_manual = True
    session.commit()

    ungroup_edition(session, e1)
    session.commit()

    assert e1.obra_manual is False
    assert e1.obra_manual_at is None
    assert e1.obra_id == auto_obra.id
    # La obra manual quedo vacia y se elimino.
    assert session.get(Obra, manual_obra.id) is None


def test_ungroup_desmarca_obra_que_conserva_ediciones() -> None:
    session = _session()
    manual_obra = _obra(session, "La vida padre", 2023, manual=True)
    auto_obra = _obra(session, "La vida padre", 2022)
    e1 = _edicion(
        session,
        "1",
        obra=manual_obra,
        titulo_uniforme="La vida padre",
        anio=2022,
    )
    e1.obra_manual = True
    e2 = _edicion(
        session,
        "2",
        obra=manual_obra,
        titulo_uniforme="La vida padre",
        anio=2023,
    )
    e2.obra_manual = True
    session.commit()

    ungroup_edition(session, e1)
    session.commit()

    assert e1.obra_id == auto_obra.id
    # La obra manual conserva e2 (manual) y sigue marcada como manual.
    assert manual_obra.manual is True
    assert session.get(Obra, manual_obra.id) is not None
