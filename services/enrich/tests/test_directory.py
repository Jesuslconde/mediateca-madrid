from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, Sucursal
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.catalog.directory import (
    DirectoryClient,
    DirectoryUnavailable,
    OpenDataDirectoryClient,
    ParsedSucursal,
    _extract_subc,
    _identity,
    _normalize_coords,
    _normalize_postcode,
    build_directory_client,
    directory_config,
    directory_mode,
    parse_directory_list,
    parse_directory_positions,
    parse_directory_record,
    parse_opendata_record,
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
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    fuente = Fuente(codigo="madrid", nombre="Madrid", base_url="https://opac.example")
    session.add(fuente)
    session.commit()
    session.info["fuente"] = fuente
    return session


def _fuente(session):
    return session.info["fuente"]


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


def test_parsea_ficha_sin_subc_sin_codigo_de_biblioteca() -> None:
    parsed = parse_directory_record(_fixture("record_no_subc.html"))

    assert parsed is not None
    assert parsed.biblioteca_codigo == ""
    assert parsed.sucursal_codigo is None
    assert parsed.nombre == "Biblioteca de Empresarios Agrupados Internacional"
    assert parsed.codigo_postal == "28015"
    assert parsed.latitud == 40.433311
    assert parsed.longitud == -3.705332


def test_parsea_coordenadas_desde_q_sin_ll() -> None:
    html = """
    <html><body>
      <div class="ficha">
        <h2>Biblioteca Regional de Madrid "Joaquín Leguina"</h2>
        <div class="direccion"><p class="ficha_valor"><span class="valor">
          C/ Ramírez de Prado, 3<br />28045 Madrid (Madrid)<br />
          <a href="http://maps.google.es/maps?q=40.399559++++,++++-3.6905689999999822&amp;hl=es">
            Mapa Localización
          </a>
        </span></p></div>
      </div>
    </body></html>
    """

    parsed = parse_directory_record(html)

    assert parsed is not None
    assert parsed.biblioteca_codigo == ""
    assert parsed.sucursal_codigo is None
    assert parsed.codigo_postal == "28045"
    assert parsed.latitud == 40.399559
    assert parsed.longitud == -3.6905689999999822


def test_parsea_coordenadas_desde_mapa_moderno_sin_ll() -> None:
    html = """
    <html><body>
      <div class="ficha">
        <h2>Biblioteca de prueba</h2>
        <div class="direccion"><p class="ficha_valor"><span class="valor">
          Calle Mayor, 1<br />28001 Madrid (Madrid)<br />
          <a href="https://www.google.com/maps/place/Calle+Mayor/@40.4155,-3.7074,17z/data=!3m1!4b1!4m5!3m4!1s0x0:0x0!8m2!3d40.4156!4d-3.7075">
            Mapa Localización
          </a>
        </span></p></div>
      </div>
    </body></html>
    """

    parsed = parse_directory_record(html)

    assert parsed is not None
    assert parsed.latitud == 40.4156
    assert parsed.longitud == -3.7075


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
    biblioteca = Biblioteca(fuente_id=_fuente(session).id, codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
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
    biblioteca = Biblioteca(fuente_id=_fuente(session).id, codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
    sucursal = Sucursal(
        fuente_id=_fuente(session).id,
        biblioteca=biblioteca,
        codigo="BMALC1",
        nombre="Cardenal Cisneros",
        codigo_postal="28801",
        latitud=40.480773,
        longitud=-3.362149,
    )
    edicion = Edicion(
        fuente_id=_fuente(session).id,
        record_id="madrid:2101557",
        titn="2101557",
        titulo="Abejas",
    )
    ejemplar = Ejemplar(
        fuente_id=_fuente(session).id,
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
    biblioteca = Biblioteca(fuente_id=_fuente(session).id, codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
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


def test_refresh_sucursales_solo_conocidas_crea_sus_sucursales() -> None:
    session = _session()
    biblioteca = Biblioteca(fuente_id=_fuente(session).id, codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá")
    sucursal = Sucursal(
        fuente_id=_fuente(session).id,
        biblioteca=biblioteca,
        codigo="BMALC1",
        nombre="Cardenal Cisneros",
    )
    session.add_all([biblioteca, sucursal])
    session.commit()

    conocida = ParsedSucursal(
        biblioteca_codigo="RBMALC",
        sucursal_codigo="BMALC1",
        nombre="Cardenal Cisneros",
        direccion="Nueva dirección, 1",
        codigo_postal="28801",
    )
    sucursal_nueva = replace(conocida, sucursal_codigo="BMALC9")
    biblioteca_nivel = ParsedSucursal(
        biblioteca_codigo="RBMALC",
        sucursal_codigo=None,
        nombre="Bibliotecas Municipales Alcalá",
        direccion="Plaza de San Julián, 1",
        codigo_postal="28801",
    )
    biblioteca_desconocida = replace(conocida, biblioteca_codigo="DESCONOCIDA")

    stats = refresh_sucursales(
        session,
        _FakeDirectoryClient(
            [conocida, sucursal_nueva, biblioteca_nivel, biblioteca_desconocida]
        ),
        fuente=_fuente(session),
        only_known=True,
    )
    session.commit()

    assert stats.records == 4
    assert stats.branches_matched == 2
    assert stats.libraries_updated == 1
    assert stats.omitted == 1
    assert session.scalar(select(func.count(Biblioteca.id))) == 1
    assert session.scalar(select(func.count(Sucursal.id))) == 2
    creada = session.scalars(
        select(Sucursal).where(Sucursal.codigo == "BMALC9")
    ).one()
    assert creada.direccion == "Nueva dirección, 1"
    assert creada.biblioteca.codigo == "RBMALC"
    assert sucursal.direccion == "Nueva dirección, 1"
    assert biblioteca.direccion == "Plaza de San Julián, 1"


def test_refresh_sucursales_empareja_por_nombre_si_falta_subc() -> None:
    session = _session()
    biblioteca = Biblioteca(
        fuente_id=_fuente(session).id,
        codigo="BRCM",
        nombre="Biblioteca Regional de Madrid Joaquín Leguina",
    )
    session.add(biblioteca)
    session.commit()

    parsed = ParsedSucursal(
        biblioteca_codigo="",
        sucursal_codigo=None,
        nombre='Biblioteca Regional de Madrid "Joaquín Leguina"',
        municipio="Madrid",
        direccion="C/ Ramírez de Prado, 3",
        codigo_postal="28045",
        latitud=40.399559,
        longitud=-3.6905689999999822,
    )
    sin_emparejar = replace(parsed, nombre="Biblioteca Desconocida")

    stats = refresh_sucursales(
        session,
        _FakeDirectoryClient([parsed, sin_emparejar]),
        fuente=_fuente(session),
        only_known=True,
    )
    session.commit()

    assert stats.records == 2
    assert stats.with_subc == 0
    assert stats.libraries_updated == 1
    assert stats.omitted == 1
    assert biblioteca.direccion == "C/ Ramírez de Prado, 3"
    assert biblioteca.codigo_postal == "28045"
    assert biblioteca.latitud == 40.399559
    assert biblioteca.longitud == -3.6905689999999822


def test_refresh_sucursales_y_cobertura() -> None:
    session = _session()
    session.add(Biblioteca(fuente_id=_fuente(session).id, codigo="RBMALC", nombre="Bibliotecas Municipales Alcalá"))
    session.commit()

    known = parse_directory_record(_fixture("record_with_coords.html"))
    library_level = parse_directory_record(_fixture("record_library_level.html"))
    assert known is not None and library_level is not None
    unknown = replace(known, biblioteca_codigo="DESCONOCIDA")
    records = [known, library_level, unknown, None]

    stats = refresh_sucursales(
        session,
        _FakeDirectoryClient(records),  # type: ignore[arg-type]
        fuente=_fuente(session),
    )
    session.commit()

    assert stats.records == 4
    assert stats.with_subc == 3
    assert stats.with_postal_code == 3
    assert stats.with_coordinates == 3
    assert stats.branches_matched == 1
    assert stats.libraries_updated == 1
    assert stats.omitted == 2
    assert session.scalar(select(func.count(Sucursal.id))) == 1


def test_fuente_sin_directorio_informa_sin_fallar() -> None:
    from mediateca_shared.models import Fuente

    session = _session()
    fuente = Fuente(
        codigo="sin-directorio",
        nombre="Sin directorio",
        base_url="https://opac.example",
        options={},
    )
    session.add(fuente)
    session.commit()

    with pytest.raises(DirectoryUnavailable):
        DirectoryClient.from_fuente(fuente)


ANDALUCIA_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "andalucia"


def _andalucia_libraries() -> list[dict]:
    import json

    return json.loads((ANDALUCIA_FIXTURES / "libraries.json").read_text(encoding="utf-8"))


def _fuente_andaluza(options: dict) -> Fuente:
    return Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        delay=1.0,
        options=options,
    )


def test_directory_config_resuelve_opendata() -> None:
    fuente = _fuente_andaluza(
        {
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
                "unit_types": ["Biblioteca"],
            }
        }
    )

    assert directory_config(fuente)["kind"] == "opendata"
    assert directory_mode(fuente) == "create"


def test_directory_config_resuelve_html_por_directory_path() -> None:
    fuente = _fuente_andaluza({"directory_path": "/directorio"})

    assert directory_config(fuente) == {"kind": "html", "path": "/directorio"}
    assert directory_mode(fuente) == "match"


def test_directory_config_sin_directorio_es_vacio() -> None:
    fuente = _fuente_andaluza({})

    assert directory_config(fuente) == {}
    assert directory_mode(fuente) == "match"


def test_build_directory_client_elige_opendata() -> None:
    fuente = _fuente_andaluza(
        {
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
            }
        }
    )

    client = build_directory_client(fuente)

    assert isinstance(client, OpenDataDirectoryClient)
    client.close()


def test_normaliza_codigo_postal() -> None:
    assert _normalize_postcode(11402) == "11402"
    assert _normalize_postcode("04001") == "04001"
    assert _normalize_postcode("04877") == "04877"
    assert _normalize_postcode(4001) == "04001"
    assert _normalize_postcode(None) is None
    assert _normalize_postcode("sin-cp") is None


def test_normaliza_coordenadas() -> None:
    assert _normalize_coords("36,6917266", "-6,1334877") == (36.6917266, -6.1334877)
    assert _normalize_coords("37.0", "-6.0") == (37.0, -6.0)
    assert _normalize_coords(None, "-6.0") == (None, None)
    assert _normalize_coords("91", "-6.0") == (None, None)
    assert _normalize_coords("0", "0") == (None, None)
    assert _normalize_coords("hola", "-6.0") == (None, None)


def test_identidad_desde_subc() -> None:
    assert _identity("CA/CA08/218", None) == ("CA/CA08", "CA/CA08/218")
    assert _identity("RBMALC/BMALC1", None) == ("RBMALC", "RBMALC/BMALC1")
    assert _identity("1432", None) == ("1432", None)
    assert _identity(None, "orbe_bibliotecas/9") == ("orbe_bibliotecas/9", None)
    assert _identity(None, None) == ("", None)


def test_extrae_subc_del_catalogo() -> None:
    url = "https://www.juntadeandalucia.es/cultura/rbpa/abnetcl.cgi?.&SUBC=CA/CA08/218"
    assert _extract_subc(url) == "CA/CA08/218"
    assert _extract_subc(None) is None
    assert _extract_subc("https://ejemplo/sin-subc") is None


def test_parse_opendata_record_deriva_identidad() -> None:
    item = {
        "icmsId": "orbe_bibliotecas/122",
        "name": "Biblioteca de prueba",
        "unit_type_name": "Biblioteca",
        "municipality_name": "Jerez de la Frontera",
        "address_name": "Avenida 10, 11402 Jerez",
        "postcode": 11402,
        "latitude": "36,6917266",
        "longitude": "-6,1334877",
        "catalogue": "https://x?SUBC=CA/CA08/218",
    }

    parsed = parse_opendata_record(item)

    assert parsed is not None
    assert parsed.biblioteca_codigo == "CA/CA08"
    assert parsed.sucursal_codigo == "CA/CA08/218"
    assert parsed.codigo_postal == "11402"
    assert parsed.latitud == 36.6917266
    assert parsed.longitud == -6.1334877
    assert parsed.movil is False


def test_parse_opendata_record_sin_subc_usa_icms_id() -> None:
    item = {
        "icmsId": "orbe_bibliotecas/501",
        "name": "Biblioteca Auxiliar",
        "unit_type_name": "Biblioteca",
        "postcode": None,
        "latitude": None,
        "longitude": None,
        "catalogue": None,
    }

    parsed = parse_opendata_record(item)

    assert parsed is not None
    assert parsed.biblioteca_codigo == "orbe_bibliotecas/501"
    assert parsed.sucursal_codigo is None
    assert parsed.codigo_postal is None
    assert parsed.latitud is None


def test_parse_opendata_record_filtra_centros_de_documentacion() -> None:
    item = {
        "icmsId": "orbe_bibliotecas/300",
        "name": "Centro de documentación",
        "unit_type_name": "Bib. Espec./Centro de Documentación",
    }

    assert parse_opendata_record(item) is None
    assert parse_opendata_record(item, unit_types=["Bib. Espec./Centro de Documentación"]) is not None


def test_parse_opendata_record_movil_sin_coordenadas() -> None:
    item = {
        "icmsId": "orbe_bibliotecas/400",
        "name": "Bibliobús - Diputación de Cádiz",
        "unit_type_name": "Biblioteca",
        "municipality_name": "Cádiz",
        "postcode": 11003,
        "latitude": "36,5350742",
        "longitude": "-6,2988132",
        "catalogue": "https://x?SUBC=CA/CA22/261",
    }

    parsed = parse_opendata_record(item)

    assert parsed is not None
    assert parsed.movil is True
    assert parsed.latitud is None
    assert parsed.longitud is None
    assert parsed.municipio == "Cádiz"
    assert parsed.codigo_postal == "11003"


def test_cliente_opendata_lee_el_fixture() -> None:
    data = _andalucia_libraries()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["format"] == "json"
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenDataDirectoryClient(
        url="https://example.test/libraries/all", delay=0, client=http_client
    )
    try:
        parsed = list(client.iter_records())
    finally:
        client.close()
        http_client.close()

    assert len(parsed) == 6
    non_null = [p for p in parsed if p is not None]
    assert len(non_null) == 5
    assert parsed[0] is not None
    assert parsed[0].biblioteca_codigo == "CA/CA08"
    assert parsed[0].sucursal_codigo == "CA/CA08/218"
    assert parsed[0].codigo_postal == "11402"
    assert parsed[0].latitud == 36.6917266


def test_cliente_opendata_sigue_la_redireccion() -> None:
    data = _andalucia_libraries()
    target = "https://example.test/download/dataset.json"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/libraries/all":
            return httpx.Response(302, headers={"Location": target})
        assert str(request.url) == target
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = OpenDataDirectoryClient(
        url="https://example.test/libraries/all", delay=0, client=http_client
    )
    try:
        parsed = list(client.iter_records())
    finally:
        client.close()
        http_client.close()

    assert len([p for p in parsed if p is not None]) == 5


def test_refresh_sucursales_create_crea_bibliotecas_y_sucursales() -> None:
    session = _session()
    andalucia = _fuente_andaluza(
        {
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
            }
        }
    )
    session.add(andalucia)
    session.commit()

    records = [
        ParsedSucursal(
            biblioteca_codigo="CA/CA08",
            sucursal_codigo="CA/CA08/218",
            nombre="Coloma",
            municipio="Jerez de la Frontera",
            direccion="Avenida 10",
            codigo_postal="11402",
            latitud=36.6,
            longitud=-6.1,
        ),
        ParsedSucursal(
            biblioteca_codigo="CA/CA08",
            sucursal_codigo="CA/CA08/219",
            nombre="Ramón de Cala",
            municipio="Jerez de la Frontera",
            direccion="Calle 1",
            codigo_postal="11402",
            latitud=36.6,
            longitud=-6.1,
        ),
    ]

    stats = refresh_sucursales(
        session, _FakeDirectoryClient(records), fuente=andalucia, create_missing=True
    )
    session.commit()

    assert stats.libraries_created == 1
    assert stats.branches_created == 2
    assert stats.branches_matched == 2
    assert session.scalar(
        select(func.count(Biblioteca.id)).where(Biblioteca.fuente_id == andalucia.id)
    ) == 1
    assert session.scalar(
        select(func.count(Sucursal.id)).where(Sucursal.fuente_id == andalucia.id)
    ) == 2
    assert session.scalar(select(func.count(Edicion.id))) == 0
    assert session.scalar(select(func.count(Ejemplar.id))) == 0

    biblioteca = session.scalars(
        select(Biblioteca).where(
            Biblioteca.fuente_id == andalucia.id,
            Biblioteca.codigo == "CA/CA08",
        )
    ).one()
    assert biblioteca.nombre == "Jerez de la Frontera"


def test_refresh_sucursales_create_es_idempotente_y_no_borra() -> None:
    session = _session()
    andalucia = _fuente_andaluza(
        {
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
            }
        }
    )
    session.add(andalucia)
    session.commit()

    def rec(codigo: str) -> ParsedSucursal:
        return ParsedSucursal(
            biblioteca_codigo="CA/CA08",
            sucursal_codigo=codigo,
            nombre=codigo,
            municipio="Jerez de la Frontera",
            codigo_postal="11402",
        )

    first = refresh_sucursales(
        session,
        _FakeDirectoryClient([rec("CA/CA08/218"), rec("CA/CA08/219")]),
        fuente=andalucia,
        create_missing=True,
    )
    session.commit()

    second = refresh_sucursales(
        session,
        _FakeDirectoryClient([rec("CA/CA08/218")]),
        fuente=andalucia,
        create_missing=True,
    )
    session.commit()

    assert first.libraries_created == 1
    assert first.branches_created == 2
    assert second.libraries_created == 0
    assert second.branches_created == 0
    assert session.scalar(
        select(func.count(Sucursal.id)).where(Sucursal.fuente_id == andalucia.id)
    ) == 2


def test_refresh_sucursales_create_no_toca_madrid() -> None:
    session = _session()
    madrid = _fuente(session)
    madrid_bib = Biblioteca(
        fuente_id=madrid.id,
        codigo="RBMALC",
        nombre="Bibliotecas Municipales Alcalá",
        municipio="Alcalá de Henares",
    )
    session.add(madrid_bib)
    session.commit()
    madrid_suc = Sucursal(
        fuente_id=madrid.id,
        biblioteca=madrid_bib,
        codigo="RBMALC/BMALC1",
        nombre="Cardenal Cisneros",
        municipio="Alcalá de Henares",
    )
    session.add(madrid_suc)
    session.commit()

    andalucia = _fuente_andaluza(
        {
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
            }
        }
    )
    session.add(andalucia)
    session.commit()

    records = [
        ParsedSucursal(
            biblioteca_codigo="CA/CA08",
            sucursal_codigo="CA/CA08/218",
            nombre="Coloma",
            municipio="Jerez de la Frontera",
            codigo_postal="11402",
        )
    ]
    refresh_sucursales(
        session, _FakeDirectoryClient(records), fuente=andalucia, create_missing=True
    )
    session.commit()

    assert session.scalar(
        select(func.count(Biblioteca.id)).where(Biblioteca.fuente_id == madrid.id)
    ) == 1
    assert session.scalar(
        select(func.count(Sucursal.id)).where(Sucursal.fuente_id == madrid.id)
    ) == 1
    assert session.scalar(
        select(func.count(Biblioteca.id)).where(Biblioteca.fuente_id == andalucia.id)
    ) == 1
    assert session.scalar(
        select(func.count(Sucursal.id)).where(Sucursal.fuente_id == andalucia.id)
    ) == 1
    assert madrid_bib.nombre == "Bibliotecas Municipales Alcalá"
    assert madrid_suc.codigo == "RBMALC/BMALC1"
