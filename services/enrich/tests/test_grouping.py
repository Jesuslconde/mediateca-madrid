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
    session.add(
        Fuente(codigo="madrid", nombre="Madrid", base_url="https://opac.example")
    )
    session.commit()
    return session


def _fuente_id(session) -> int:
    return session.scalar(select(Fuente.id))


def _obra(session, titulo: str, anio: int | None) -> Obra:
    obra = Obra(titulo_uniforme=titulo, anio=anio)
    session.add(obra)
    session.flush()
    return obra


def _edicion(
    session,
    titn: str,
    *,
    titulo: str,
    titulo_uniforme: str | None = None,
    anio: int | None = None,
    obra: Obra | None = None,
) -> Edicion:
    edicion = Edicion(
        fuente_id=_fuente_id(session),
        record_id=f"madrid:{titn}",
        titn=titn,
        titulo=titulo,
        titulo_uniforme=titulo_uniforme,
        anio=anio,
        obra=obra,
    )
    session.add(edicion)
    session.flush()
    return edicion


def test_agrupar_mueve_ediciones_y_marca_toda_la_obra() -> None:
    session = _session()
    destino = _obra(session, "La vida padre", 2022)
    hermana = _edicion(
        session,
        "1",
        titulo="La vida padre",
        titulo_uniforme="La vida padre",
        anio=2022,
        obra=destino,
    )
    origen_a = _obra(session, "La vida padre (DVD)", 2022)
    origen_b = _obra(session, "La vida padre (Blu-ray)", 2022)
    primera = _edicion(
        session,
        "2",
        titulo="La vida padre",
        titulo_uniforme="La vida padre (DVD)",
        anio=2022,
        obra=origen_a,
    )
    segunda = _edicion(
        session,
        "3",
        titulo="La vida padre",
        titulo_uniforme="La vida padre (Blu-ray)",
        anio=2022,
        obra=origen_b,
    )
    session.commit()

    afectadas = group_editions_into_obra(session, [primera, segunda], destino)
    session.commit()

    assert afectadas == ["madrid:2", "madrid:3"]
    assert primera.obra_id == destino.id
    assert segunda.obra_id == destino.id
    assert hermana.obra_manual is True
    assert primera.obra_manual is True
    assert segunda.obra_manual is True
    assert primera.obra_manual_at is not None
    assert destino.manual is True
    assert session.scalar(select(func.count(Obra.id))) == 1


def test_agrupar_no_elimina_la_obra_origen_con_ediciones() -> None:
    session = _session()
    destino = _obra(session, "Destino", 2000)
    origen = _obra(session, "Origen", 2001)
    primera = _edicion(
        session, "1", titulo="Uno", titulo_uniforme="Origen", anio=2001, obra=origen
    )
    permanece = _edicion(
        session, "2", titulo="Dos", titulo_uniforme="Origen", anio=2001, obra=origen
    )
    session.commit()

    group_editions_into_obra(session, [primera], destino)
    session.commit()

    assert session.get(Obra, origen.id) is not None
    assert permanece.obra_id == origen.id
    assert primera.obra_id == destino.id


def test_crear_obra_reutiliza_la_clave_existente() -> None:
    session = _session()
    existente = _obra(session, "La vida padre", 2022)
    edicion_existente = _edicion(
        session,
        "1",
        titulo="La vida padre",
        titulo_uniforme="La vida padre",
        anio=2022,
        obra=existente,
    )
    otra = _edicion(session, "2", titulo="La vida padre")
    session.commit()

    obra, afectadas = create_obra_and_group(
        session, [edicion_existente, otra], "La vida padre", 2022
    )
    session.commit()

    assert obra.id == existente.id
    assert afectadas == ["madrid:1", "madrid:2"]
    assert session.scalar(select(func.count(Obra.id))) == 1
    assert otra.obra_id == existente.id
    assert obra.manual is True


def test_desvincular_recalcula_la_obra_y_desmarca_la_anterior() -> None:
    session = _session()
    manual = _obra(session, "Agrupacion manual", 2022)
    edicion = _edicion(
        session,
        "1",
        titulo="La vida padre",
        titulo_uniforme="La vida padre",
        anio=2022,
        obra=manual,
    )
    session.commit()

    group_editions_into_obra(session, [edicion], manual)
    session.commit()
    assert manual.manual is True

    record_id = ungroup_edition(session, edicion)
    session.commit()

    assert record_id == "madrid:1"
    assert edicion.obra_manual is False
    assert edicion.obra_manual_at is None
    assert edicion.obra.titulo_uniforme == "La vida padre"
    assert edicion.obra.id != manual.id
    assert edicion.obra.manual is False
    assert session.get(Obra, manual.id) is None


def test_desvincular_mantiene_manual_si_quedan_ediciones_manuales() -> None:
    session = _session()
    manual = _obra(session, "Agrupacion manual", 2022)
    primera = _edicion(
        session, "1", titulo="Una", titulo_uniforme="Una", anio=2022, obra=manual
    )
    segunda = _edicion(
        session, "2", titulo="Dos", titulo_uniforme="Dos", anio=2022, obra=manual
    )
    session.commit()
    group_editions_into_obra(session, [primera, segunda], manual)
    session.commit()

    ungroup_edition(session, primera)
    session.commit()

    assert manual.manual is True
    assert segunda.obra_manual is True
    assert primera.obra_manual is False
