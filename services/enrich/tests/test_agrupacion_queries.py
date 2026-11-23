from __future__ import annotations

from mediateca_shared.models import Edicion, Fuente, Obra
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.core.db import Base
from mediateca.dashboard.agrupacion_queries import (
    AgrupacionFilter,
    agrupacion_rows,
    agrupacion_summary,
    agrupacion_total,
    obra_candidates,
)


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
    session.info["fuente_id"] = session.query(Fuente.id).one()[0]
    return session


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
    soporte: str | None = None,
    obra: Obra | None = None,
    manual: bool = False,
) -> Edicion:
    edicion = Edicion(
        fuente_id=session.info["fuente_id"],
        record_id=f"madrid:{titn}",
        titn=titn,
        titulo=titulo,
        titulo_uniforme=titulo,
        anio=obra.anio if obra else None,
        soporte_principal=soporte,
        obra=obra,
        obra_manual=manual,
    )
    session.add(edicion)
    session.flush()
    return edicion


def test_filtra_por_texto_fuente_soporte_y_estado() -> None:
    session = _session()
    obra = _obra(session, "La vida padre", 2022)
    _edicion(session, "1", titulo="La vida padre", soporte="DVD", obra=obra)
    _edicion(session, "2", titulo="La vida padre", soporte="Blu-ray", obra=obra, manual=True)
    _edicion(session, "3", titulo="Otra pelicula", soporte="DVD")
    session.commit()

    assert [e.titn for e in agrupacion_rows(session, AgrupacionFilter(texto="vida", amplio=True))] == [
        "1",
        "2",
    ]
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(soporte="Blu-ray"))
    ] == ["2"]
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(fuente="madrid"))
    ] == ["1", "2", "3"]
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(estado="manual"))
    ] == ["2"]
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(estado="sin_obra"))
    ] == ["3"]
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(estado="automatica"))
    ] == ["1"]


def test_texto_es_exacto_por_defecto_y_amplio_es_opcional() -> None:
    session = _session()
    obra = _obra(session, "La vida padre", 2022)
    _edicion(session, "1", titulo="La vida padre", obra=obra)
    _edicion(session, "2", titulo="La vida padre", obra=obra)
    _edicion(session, "3", titulo="Otra pelicula")
    session.commit()

    # Por defecto el texto es exacto: "vida" no coincide con "La vida padre".
    assert agrupacion_rows(session, AgrupacionFilter(texto="vida")) == []
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(texto="La vida padre"))
    ] == ["1", "2"]
    # Con ``amplio`` se recupera la búsqueda por coincidencia parcial.
    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(texto="vida", amplio=True))
    ] == ["1", "2"]


def test_filtra_por_anio() -> None:
    session = _session()
    obra = _obra(session, "La vida padre", 2022)
    _edicion(session, "1", titulo="La vida padre", obra=obra)
    _edicion(session, "2", titulo="La vida padre", obra=obra)
    _edicion(session, "3", titulo="Otra pelicula")
    session.commit()

    assert [
        e.titn for e in agrupacion_rows(session, AgrupacionFilter(anio=2022))
    ] == ["1", "2"]
    assert agrupacion_rows(session, AgrupacionFilter(anio=1999)) == []


def test_resumen_separa_estados_y_respeta_filtros_base() -> None:
    session = _session()
    obra = _obra(session, "La vida padre", 2022)
    _edicion(session, "1", titulo="La vida padre", obra=obra)
    _edicion(session, "2", titulo="La vida padre", obra=obra, manual=True)
    _edicion(session, "3", titulo="Otra")
    session.commit()

    resumen = agrupacion_summary(session, AgrupacionFilter())
    assert resumen.total == 3
    assert resumen.sin_obra == 1
    assert resumen.automatica == 1
    assert resumen.manual == 1

    filtrado = agrupacion_summary(session, AgrupacionFilter(texto="vida", amplio=True))
    assert filtrado.total == 2
    assert filtrado.sin_obra == 0
    assert filtrado.manual == 1
    assert agrupacion_total(session, AgrupacionFilter(texto="vida", amplio=True)) == 2


def test_paginacion_estable_y_limite() -> None:
    session = _session()
    for titn in ("1", "2", "3"):
        _edicion(session, titn, titulo=f"Pelicula {titn}")
    session.commit()

    primera = agrupacion_rows(session, AgrupacionFilter(page=1, limit=2))
    segunda = agrupacion_rows(session, AgrupacionFilter(page=2, limit=2))

    assert [e.titn for e in primera] == ["1", "2"]
    assert [e.titn for e in segunda] == ["3"]
    assert agrupacion_total(session, AgrupacionFilter()) == 3


def test_obras_candidatas_solo_con_texto_y_maximo_20() -> None:
    session = _session()
    for number in range(25):
        _obra(session, f"La vida padre {number:02d}", 2022 + number)
    session.commit()

    assert obra_candidates(session, None) == []
    assert obra_candidates(session, "   ") == []

    candidatas = obra_candidates(session, "vida padre")
    assert len(candidatas) == 20
    assert all("vida padre" in candidata.obra.titulo_uniforme.lower() for candidata in candidatas)

    por_anio = obra_candidates(session, "2022")
    assert [candidata.obra.titulo_uniforme for candidata in por_anio] == [
        "La vida padre 00"
    ]
