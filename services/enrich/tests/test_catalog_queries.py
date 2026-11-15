from __future__ import annotations

from datetime import UTC, datetime

from mediateca_shared.models import Biblioteca, Edicion, Ejemplar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.jobs import create_stub
from mediateca.core.db import Base
from mediateca.dashboard.catalog_queries import (
    CatalogFilter,
    catalog_rows,
    catalog_summary,
    catalog_total,
)


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _edicion(
    session,
    titn,
    *,
    titulo=None,
    anio=None,
    idioma=None,
    pais=None,
    soporte=None,
    enrich_status="pending",
    tmdb_status="pending",
    missing=False,
) -> Edicion:
    edicion = create_stub(session, titn)
    edicion.titulo = titulo or titn
    edicion.anio = anio
    edicion.idioma = idioma
    edicion.pais = pais
    edicion.soporte_principal = soporte
    edicion.enrich_status = enrich_status
    edicion.tmdb_status = tmdb_status
    if missing:
        edicion.missing_at = datetime.now(UTC)
    session.flush()
    return edicion


def test_filtro_por_estado_opac() -> None:
    session = _session()
    _edicion(session, "1", enrich_status="failed")
    _edicion(session, "2", enrich_status="enriched")
    session.commit()

    rows = catalog_rows(session, CatalogFilter(enrich_status="failed"))

    assert [edicion.titn for edicion in rows] == ["1"]


def test_filtro_por_estado_tmdb() -> None:
    session = _session()
    _edicion(session, "1", tmdb_status="unmatched")
    _edicion(session, "2", tmdb_status="matched")
    session.commit()

    rows = catalog_rows(session, CatalogFilter(tmdb_status="unmatched"))

    assert [edicion.titn for edicion in rows] == ["1"]


def test_filtro_por_desaparicion() -> None:
    session = _session()
    _edicion(session, "1", missing=True)
    _edicion(session, "2", missing=False)
    session.commit()

    assert [e.titn for e in catalog_rows(session, CatalogFilter(missing="solo"))] == ["1"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(missing="excluir"))] == ["2"]


def test_filtro_por_texto_y_campos() -> None:
    session = _session()
    _edicion(session, "1", titulo="Amanece", anio=2002, idioma="es", pais="ES", soporte="DVD")
    _edicion(session, "2", titulo="Anochece", anio=2010, idioma="en", pais="US", soporte="Blu-ray")
    session.commit()

    assert [e.titn for e in catalog_rows(session, CatalogFilter(texto="amanece"))] == ["1"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(soporte="Blu-ray"))] == ["2"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(anio_desde=2005))] == ["2"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(anio_hasta=2005))] == ["1"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(idioma="es"))] == ["1"]
    assert [e.titn for e in catalog_rows(session, CatalogFilter(pais="US"))] == ["2"]


def test_filtro_por_biblioteca_no_duplica() -> None:
    session = _session()
    biblio = Biblioteca(codigo="B1", nombre="Central")
    session.add(biblio)
    session.flush()

    edicion = _edicion(session, "1")
    for key in ("k1", "k2"):
        session.add(Ejemplar(external_key=key, biblioteca=biblio, edicion=edicion))
    session.flush()

    _edicion(session, "2")
    session.commit()

    rows = catalog_rows(session, CatalogFilter(biblioteca="B1"))

    assert [e.titn for e in rows] == ["1"]
    assert catalog_total(session, CatalogFilter(biblioteca="B1")) == 1


def test_resumen_vacio_y_con_filtro() -> None:
    session = _session()
    vacio = catalog_summary(session, CatalogFilter())
    assert vacio.total == 0
    assert all(count == 0 for count in vacio.por_enrich.values())
    assert all(count == 0 for count in vacio.por_tmdb.values())
    assert vacio.desaparecidas == 0

    _edicion(session, "1", enrich_status="enriched", tmdb_status="matched")
    _edicion(session, "2", enrich_status="failed", tmdb_status="unmatched")
    session.commit()

    resumen = catalog_summary(session, CatalogFilter(enrich_status="failed"))
    assert resumen.total == 1
    assert resumen.por_enrich["failed"] == 1
    assert resumen.por_enrich["enriched"] == 0
    assert resumen.por_tmdb["unmatched"] == 1
    assert resumen.por_tmdb["matched"] == 0


def test_paginacion_estable_y_limite_acotado() -> None:
    session = _session()
    for titn in ("1", "2", "3", "4", "5"):
        _edicion(session, titn)
    session.commit()

    filtro = CatalogFilter(page=1, limit=2)
    assert [e.titn for e in catalog_rows(session, filtro)] == ["1", "2"]
    assert catalog_total(session, filtro) == 5

    filtro2 = CatalogFilter(page=2, limit=2)
    assert [e.titn for e in catalog_rows(session, filtro2)] == ["3", "4"]
    assert catalog_total(session, filtro2) == 5

    acotado = catalog_rows(session, CatalogFilter(page=1, limit=0))
    assert len(acotado) == 1

    todos = catalog_rows(session, CatalogFilter(page=1, limit=500))
    assert [e.titn for e in todos] == ["1", "2", "3", "4", "5"]
