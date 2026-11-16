from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import httpx
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Sucursal
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.directory import (
    DirectoryClient,
    ParsedSucursal,
    parse_directory_list,
    parse_directory_positions,
    parse_directory_record,
    refresh_sucursales,
)
from mediateca.catalog.repository import (
    update_biblioteca_location,
    upsert_sucursal,
)
from mediateca.core.db import Base

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "directory"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_parsea_listado_y_paginacion() -> None:
    html = _fixture("list_page.html")

    assert parse_directory_list(html) == ["65", "59"]
    assert parse_directory_positions(html) == [51, 101]


def test_parsea_ficha_con_coordenadas() -> None:
    parsed = parse_directory_record(_fixture("record_with_coords.html"))

    assert parsed is not None
    assert parsed.biblioteca_codigo == "RBMALC"
    assert parsed.sucursal_codigo == "BMALC1"
    assert parsed.nombre == 'Biblioteca Municipal "Cardenal Cisneros"'
    assert parsed.municipio == "Alcalá de Henares"
    assert parsed.direccion == "Plaza de San Julián, 1"
    assert parsed.codigo_postal == "28801"
    assert parsed.latitud == 40.480773
    assert parsed.longitud == -3.362149
    assert parsed.movil is False


def test_ignora_el_centro_sll_y_usa_ll() -> None:
    parsed = parse_directory_record(_fixture("record_with_coords.html"))

    assert parsed is not None
    assert parsed.latitud != 36.552241
    assert parsed.longitud != -4.615889


def test_parsea_ficha_sin_coordenadas() -> None:
    parsed = parse_directory_record(_fixture("record_without_coords.html"))

    assert parsed is not None
    assert parsed.sucursal_codigo == "BMALC3"
    assert parsed.codigo_postal == "28801"
    assert parsed.municipio == "Alcalá de Henares"
    assert parsed.latitud is None
    assert parsed.longitud is None


def test_omite_ficha_sin_subc() -> None:
    assert parse_directory_record(_fixture("record_no_subc.html")) is None


def test_omite_ficha_cerrada() -> None:
    assert parse_directory_record(_fixture("record_closed.html")) is None


def test_parsea_biblioteca_movil_sin_coordenadas_de_paradas() -> None:
    parsed = parse_directory_record(_fixture("record_mobile.html"))

    assert parsed is not None
    assert parsed.movil is True
    assert parsed.biblioteca_codigo == "MUNI"
    assert parsed.sucursal_codigo == "BB01"
    assert parsed.codigo_postal == "28021"
    assert parsed.municipio == "Madrid"
    assert parsed.latitud is None
    assert parsed.longitud is None


def test_parsea_ficha_de_ambito_de_biblioteca() -> None:
    parsed = parse_directory_record(_fixture("record_library_level.html"))

    assert parsed is not None
    assert parsed.biblioteca_codigo == "RBMALC"
    assert parsed.sucursal_codigo is None
    assert parsed.latitud == 40.48156
    assert parsed.longitud == -3.36521


def test_enlace_corto_no_aporta_coordenadas() -> None:
    html = """
    <html><body>
      <div class="ficha">
        <h2>Biblioteca de prueba</h2>
        <div class="direccion"><p class="ficha_valor"><span class="valor">
          Calle Mayor, 1<br />28001 Madrid (Madrid)<br />
          <a href="https://maps.app.goo.gl/abc123">Mapa Localización</a><br />
          <a href="https://opac?SUBC=RBMX/BMX1">Catálogo</a>
        </span></p></div>
      </div>
    </body></html>
    """

    parsed = parse_directory_record(html)

    assert parsed is not None
    assert parsed.codigo_postal == "28001"
    assert parsed.latitud is None
    assert parsed.longitud is None


def test_cliente_pagina_y_limita() -> None:
    first_page = _fixture("list_page.html")
    second_page = '<a class="indice_registros" href="registro.cmd?id=60">Biblioteca</a>'
    records = {
        "65": _fixture("record_with_coords.html"),
        "59": _fixture("record_with_coords.html"),
        "60": _fixture("record_without_coords.html"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "posicion=51" in url:
            return httpx.Response(200, text=second_page)
        if "registro.cmd?id=" in url:
            record_id = request.url.params["id"]
            return httpx.Response(200, text=records[record_id])
        return httpx.Response(200, text=first_page)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        transport=transport, base_url="https://example.test/directorio"
    )
    client = DirectoryClient(
        base_url="https://example.test/directorio", delay=0, client=http_client
    )
    try:
        assert list(client.iter_record_ids(max_pages=2)) == ["65", "59", "60"]
        parsed = list(client.iter_records(limit=2, max_pages=2))
        assert len(parsed) == 2
        assert all(item is not None for item in parsed)
    finally:
        client.close()
        http_client.close()


def test_cliente_reintenta_error_temporal() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(500, text="error")
        return httpx.Response(200, text=_fixture("list_page.html"))

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        transport=transport, base_url="https://example.test/directorio"
    )
    client = DirectoryClient(
        base_url="https://example.test/directorio", delay=0, client=http_client
    )
    try:
        assert "registro.cmd?id=65" in client.fetch_list_page()
        assert attempts["count"] == 2
    finally:
        client.close()
        http_client.close()


def test_upsert_sucursal_es_idempotente_y_no_pisa_coordenadas() -> None:
    session = _session()
    biblioteca = Biblioteca(codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
    session.add(biblioteca)
    session.commit()

    parsed = parse_directory_record(_fixture("record_with_coords.html"))
    assert parsed is not None
    first = upsert_sucursal(session, biblioteca, parsed)
    session.commit()

    second = upsert_sucursal(session, biblioteca, replace(parsed, latitud=None, longitud=None))
    session.commit()

    assert first.id == second.id
    assert session.scalar(select(func.count(Sucursal.id))) == 1
    assert second.latitud == 40.480773
    assert second.longitud == -3.362149
    assert second.codigo_postal == "28801"


def test_ejemplar_resuelve_sucursal_por_codigo() -> None:
    session = _session()
    biblioteca = Biblioteca(codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
    sucursal = Sucursal(
        biblioteca=biblioteca,
        codigo="BMALC1",
        nombre="Cardenal Cisneros",
        codigo_postal="28801",
        latitud=40.480773,
        longitud=-3.362149,
    )
    edicion = Edicion(titn="2101557", titulo="Abejas")
    ejemplar = Ejemplar(
        edicion=edicion,
        biblioteca=biblioteca,
        external_key="k1",
        sucursal_codigo="BMALC1",
        sucursal_nombre="Cardenal Cisneros",
    )
    session.add_all([biblioteca, sucursal, edicion, ejemplar])
    session.commit()

    loaded = session.scalars(
        select(Edicion).options(
            selectinload(Edicion.ejemplares).selectinload(Ejemplar.sucursal)
        )
    ).one()

    assert loaded.ejemplares[0].sucursal is not None
    assert loaded.ejemplares[0].sucursal.codigo == "BMALC1"
    assert loaded.ejemplares[0].sucursal.latitud == 40.480773


def test_update_biblioteca_location() -> None:
    session = _session()
    biblioteca = Biblioteca(codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
    session.add(biblioteca)
    session.commit()

    parsed = ParsedSucursal(
        biblioteca_codigo="RBMALC",
        sucursal_codigo=None,
        nombre="Bibliotecas Municipales Alcalá",
        municipio="Alcalá de Henares",
        direccion="Plaza de San Julián, 1",
        codigo_postal="28801",
        latitud=40.48156,
        longitud=-3.36521,
    )
    update_biblioteca_location(session, biblioteca, parsed)
    session.commit()

    assert biblioteca.municipio == "Alcalá de Henares"
    assert biblioteca.direccion == "Plaza de San Julián, 1"
    assert biblioteca.codigo_postal == "28801"
    assert biblioteca.latitud == 40.48156
    assert biblioteca.longitud == -3.36521


class _FakeDirectoryClient:
    def __init__(self, records: list[ParsedSucursal | None]) -> None:
        self.records = records

    def iter_records(self, *, limit=None, max_pages=None):  # noqa: ANN001, ANN201
        yield from self.records


def test_refresh_sucursales_y_cobertura() -> None:
    session = _session()
    session.add(Biblioteca(codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá"))
    session.commit()

    known = parse_directory_record(_fixture("record_with_coords.html"))
    library_level = parse_directory_record(_fixture("record_library_level.html"))
    assert known is not None and library_level is not None
    unknown = replace(known, biblioteca_codigo="DESCONOCIDA")
    records = [known, library_level, unknown, None]

    stats = refresh_sucursales(session, _FakeDirectoryClient(records))  # type: ignore[arg-type]
    session.commit()

    assert stats.records == 4
    assert stats.with_subc == 3
    assert stats.with_postal_code == 3
    assert stats.with_coordinates == 3
    assert stats.branches_matched == 1
    assert stats.libraries_updated == 1
    assert stats.omitted == 2
    assert session.scalar(select(func.count(Sucursal.id))) == 1
