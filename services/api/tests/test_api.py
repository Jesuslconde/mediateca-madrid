from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from mediateca_shared.db import Base
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, Obra, Sucursal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.api.deps import get_db, get_indexer
from mediateca.api.main import app
from mediateca.catalog.search import CatalogSearch


class _DummyIndexer:
    def search(self, *args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("No se debe consultar el indice con un filtro retirado")


def test_search_rechaza_parametro_disponible() -> None:
    app.dependency_overrides[get_indexer] = lambda: _DummyIndexer()
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"disponible": "true"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "disponibilidad" in response.json()["detail"].lower()


class _FakeMeiliIndex:
    def __init__(self) -> None:
        self.options: dict | None = None

    def search(self, query, options):  # noqa: ANN001
        self.options = options
        return {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 0,
            "facetDistribution": {},
        }


def _indexer_override(indexer: CatalogSearch):
    def override() -> CatalogSearch:
        return indexer

    return override


def _catalog_search() -> tuple[CatalogSearch, _FakeMeiliIndex]:
    index = _FakeMeiliIndex()
    search = CatalogSearch.__new__(CatalogSearch)
    search.client = object()
    search.index = index
    return search, index


def test_search_filtra_solo_fichas_enriquecidas() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"q": "cine"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert "detail_complete = true" in index.options["filter"]


def test_search_filtra_por_titn() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"titn": "2101557"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == 'detail_complete = true AND titn = "2101557"'


def test_search_combina_filtro_de_enriquecidas_con_faceta() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"q": "cine", "genero": "Drama"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert "detail_complete = true" in index.options["filter"]
    assert 'generos = "Drama"' in index.options["filter"]


def test_search_filtra_por_un_pais_de_origen() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"q": "cine", "paises_origen": "ES"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert "detail_complete = true" in index.options["filter"]
    assert 'paises_origen = "ES"' in index.options["filter"]


def test_search_combina_varios_paises_con_or() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search",
            params=[("q", "cine"), ("paises_origen", "ES"), ("paises_origen", "FR")],
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND (paises_origen = "ES" OR paises_origen = "FR")'
    )
    assert "paises_origen" in index.options["facets"]


def test_search_filtra_por_biblioteca_sin_idioma() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search",
            params={
                "biblioteca": "Biblioteca Regional de Madrid Joaquín Leguina",
                "idioma": "",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        "detail_complete = true AND "
        '(bibliotecas = "Biblioteca Regional de Madrid Joaquín Leguina" OR '
        'ubicaciones_texto = "Biblioteca Regional de Madrid Joaquín Leguina")'
    )


def test_search_combina_biblioteca_e_idioma() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search",
            params={
                "biblioteca": "Biblioteca Regional de Madrid Joaquín Leguina",
                "idioma": "es",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND idioma = "es" AND '
        '(bibliotecas = "Biblioteca Regional de Madrid Joaquín Leguina" OR '
        'ubicaciones_texto = "Biblioteca Regional de Madrid Joaquín Leguina")'
    )


def test_search_filtra_por_codigo_de_ubicacion() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"biblioteca": "s:madrid:BMALC1"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND ubicaciones = "s:madrid:BMALC1"'
    )


def test_search_filtra_por_nombre_de_sucursal() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search", params={"biblioteca": "B.P.M. Cardenal Cisneros"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND '
        '(bibliotecas = "B.P.M. Cardenal Cisneros" OR '
        'ubicaciones_texto = "B.P.M. Cardenal Cisneros")'
    )


def test_search_combina_pais_con_genero_y_enriquecidas() -> None:
    search, index = _catalog_search()
    app.dependency_overrides[get_indexer] = lambda: search
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search",
            params={"q": "cine", "genero": "Drama", "paises_origen": "ES"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND generos = "Drama" AND (paises_origen = "ES")'
    )


class _CapturingIndexer:
    def __init__(self) -> None:
        self.kwargs: dict | None = None

    def search(self, query, **kwargs):  # noqa: ANN001, ANN003
        self.kwargs = kwargs
        return {
            "query": query,
            "page": 1,
            "limit": 20,
            "total": 0,
            "total_pages": 1,
            "took_ms": 0,
            "facets": {},
            "hits": [],
        }


def test_router_propaga_paises_origen_al_adaptador() -> None:
    indexer = _CapturingIndexer()
    app.dependency_overrides[get_indexer] = lambda: indexer
    try:
        client = TestClient(app)
        response = client.get(
            "/api/search",
            params=[("paises_origen", "ES"), ("paises_origen", "FR")],
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert indexer.kwargs is not None
    assert indexer.kwargs["paises_origen"] == ["ES", "FR"]


class _FakeScalars:
    def __init__(self, edicion: Edicion) -> None:
        self.edicion = edicion

    def first(self) -> Edicion:
        return self.edicion


class _FakeSession:
    def __init__(self, edicion: Edicion) -> None:
        self.edicion = edicion

    def scalars(self, stmt):  # noqa: ANN001
        return _FakeScalars(self.edicion)


def _edicion(
    paises_origen: list[str],
    *,
    tmdb_poster_url: str | None = None,
    tmdb_url: str | None = None,
) -> Edicion:
    edicion = Edicion(
        record_id="madrid:2101557",
        titn="2101557",
        titulo="Abejas",
        paises_origen=paises_origen,
        tmdb_poster_url=tmdb_poster_url,
        tmdb_url=tmdb_url,
    )
    edicion.materias = []
    edicion.personas = []
    edicion.enlaces = []
    edicion.ejemplares = []
    edicion.obra = None
    edicion.updated_at = None
    return edicion


def _get_record(
    paises_origen: list[str],
    *,
    tmdb_poster_url: str | None = None,
    tmdb_url: str | None = None,
):
    edicion = _edicion(
        paises_origen,
        tmdb_poster_url=tmdb_poster_url,
        tmdb_url=tmdb_url,
    )
    app.dependency_overrides[get_db] = lambda: _FakeSession(edicion)
    try:
        client = TestClient(app)
        return client.get("/api/records/2101557")
    finally:
        app.dependency_overrides.clear()


def test_record_devuelve_paises_de_origen() -> None:
    response = _get_record(["ES", "FR"])

    assert response.status_code == 200
    assert response.json()["paises_origen"] == ["ES", "FR"]


def test_record_sin_paises_devuelve_lista_vacia() -> None:
    response = _get_record([])

    assert response.status_code == 200
    assert response.json()["paises_origen"] == []


def test_record_de_cobertura_sin_ejemplares_expone_source_url() -> None:
    session = _sqlite_session()
    fuente = Fuente(
        codigo="cataluna",
        nombre="Cataluna",
        base_url="https://catalogos.cultura.gob.es",
        opac_path="/CCBIP/cgi-ccbip/abnetopac",
    )
    session.add(fuente)
    session.commit()
    session.add(
        Edicion(
            fuente_id=fuente.id,
            record_id="cataluna:18",
            titn="18",
            titulo="007 al servicio secreto de su majestad",
        )
    )
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/records/cataluna:18")
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert response.status_code == 200
    body = response.json()
    assert body["fuente"] == "cataluna"
    assert body["ejemplares"] == []
    assert body["source_url"] == (
        "https://catalogos.cultura.gob.es/CCBIP/cgi-ccbip/abnetopac?TITN=18"
    )


def test_record_devuelve_portada_y_enlace_de_tmdb() -> None:
    response = _get_record(
        ["ES"],
        tmdb_poster_url="https://image.tmdb.org/t/p/w500/poster.jpg",
        tmdb_url="https://www.themoviedb.org/movie/10",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tmdb_poster_url"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert body["tmdb_url"] == "https://www.themoviedb.org/movie/10"


def _sqlite_session():
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


def _record_with_location(
    *,
    with_sucursal: bool = True,
    sucursal_coords: bool = True,
    biblioteca_coords: bool = True,
):
    session = _sqlite_session()
    biblioteca = Biblioteca(
        fuente_id=_fuente(session).id,
        codigo="RBMALC",
        nombre="Bibliotecas Municipales Alcalá",
        municipio="Alcalá de Henares",
        codigo_postal="28801",
        latitud=40.48156 if biblioteca_coords else None,
        longitud=-3.36521 if biblioteca_coords else None,
    )
    edicion = Edicion(
        fuente_id=_fuente(session).id,
        record_id="madrid:2101557",
        titn="2101557",
        titulo="Abejas",
    )
    session.add_all([biblioteca, edicion])
    if with_sucursal:
        session.add(
            Sucursal(
                fuente_id=_fuente(session).id,
                biblioteca=biblioteca,
                codigo="BMALC1",
                nombre="Cardenal Cisneros",
                municipio="Alcalá de Henares",
                codigo_postal="28801",
                latitud=40.480773 if sucursal_coords else None,
                longitud=-3.362149 if sucursal_coords else None,
            )
        )
    session.add(
        Ejemplar(
            fuente_id=_fuente(session).id,
            edicion=edicion,
            biblioteca=biblioteca,
            external_key="k1",
            sucursal_codigo="BMALC1" if with_sucursal else None,
            sucursal_nombre="Cardenal Cisneros" if with_sucursal else None,
        )
    )
    session.commit()
    return session


def _get_record_with_session(session):
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        return client.get("/api/records/2101557")
    finally:
        app.dependency_overrides.clear()


def test_locations_incluye_biblioteca_y_sucursal() -> None:
    session = _record_with_location()
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/locations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    locations = {item["codigo"]: item for item in response.json()}
    assert set(locations) == {"b:madrid:RBMALC", "s:madrid:BMALC1"}

    biblioteca = locations["b:madrid:RBMALC"]
    assert biblioteca["tipo"] == "biblioteca"
    assert biblioteca["nombre"] == "Bibliotecas Municipales Alcalá"
    assert biblioteca["biblioteca_codigo"] == "RBMALC"
    assert biblioteca["ejemplares"] == 1

    sucursal = locations["s:madrid:BMALC1"]
    assert sucursal["tipo"] == "sucursal"
    assert sucursal["nombre"] == "Cardenal Cisneros"
    assert sucursal["biblioteca_codigo"] == "RBMALC"
    assert sucursal["biblioteca_nombre"] == "Bibliotecas Municipales Alcalá"
    assert sucursal["ejemplares"] == 1


def test_locations_sin_sucursal_solo_devuelve_biblioteca() -> None:
    session = _record_with_location(with_sucursal=False)
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/locations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [item["codigo"] for item in response.json()] == ["b:madrid:RBMALC"]


def test_locations_incluye_sucursal_sin_fila_en_sucursales() -> None:
    session = _sqlite_session()
    biblioteca = Biblioteca(
        fuente_id=_fuente(session).id,
        codigo="BPM",
        nombre="MADRID. Bibliotecas Públicas",
        municipio="Madrid",
    )
    edicion = Edicion(
        fuente_id=_fuente(session).id,
        record_id="madrid:1948243",
        titn="1948243",
        titulo="Dolor y gloria",
    )
    ejemplar = Ejemplar(
        fuente_id=_fuente(session).id,
        edicion=edicion,
        biblioteca=biblioteca,
        external_key="k1",
        sucursal_codigo="BP20",
        sucursal_nombre="VILLA DE VALLECAS. BP Luis Martín Santos",
    )
    session.add_all([biblioteca, edicion, ejemplar])
    session.commit()
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/locations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    locations = {item["codigo"]: item for item in response.json()}
    assert locations["s:madrid:BP20"]["nombre"] == "VILLA DE VALLECAS. BP Luis Martín Santos"
    assert locations["s:madrid:BP20"]["biblioteca_codigo"] == "BPM"
    assert locations["s:madrid:BP20"]["municipio"] == "Madrid"


def test_record_incluye_ubicacion_de_sucursal() -> None:
    session = _record_with_location()
    try:
        response = _get_record_with_session(session)
    finally:
        session.close()

    assert response.status_code == 200
    ubicacion = response.json()["ejemplares"][0]["ubicacion"]
    assert ubicacion == {
        "codigo_postal": "28801",
        "municipio": "Alcalá de Henares",
        "latitud": 40.480773,
        "longitud": -3.362149,
    }


def test_record_ubicacion_solo_codigo_postal() -> None:
    session = _record_with_location(sucursal_coords=False)
    try:
        response = _get_record_with_session(session)
    finally:
        session.close()

    assert response.status_code == 200
    ubicacion = response.json()["ejemplares"][0]["ubicacion"]
    assert ubicacion["codigo_postal"] == "28801"
    assert ubicacion["latitud"] is None
    assert ubicacion["longitud"] is None


def test_record_ubicacion_fallback_biblioteca() -> None:
    session = _record_with_location(with_sucursal=False)
    try:
        response = _get_record_with_session(session)
    finally:
        session.close()

    assert response.status_code == 200
    ubicacion = response.json()["ejemplares"][0]["ubicacion"]
    assert ubicacion["codigo_postal"] == "28801"
    assert ubicacion["latitud"] == 40.48156
    assert ubicacion["longitud"] == -3.36521


def test_record_sin_ubicacion() -> None:
    session = _record_with_location(
        with_sucursal=False, biblioteca_coords=False
    )
    biblioteca = session.query(Biblioteca).one()
    biblioteca.municipio = None
    biblioteca.codigo_postal = None
    session.commit()
    try:
        response = _get_record_with_session(session)
    finally:
        session.close()

    assert response.status_code == 200
    assert response.json()["ejemplares"][0]["ubicacion"] is None


def test_openapi_incluye_ubicacion_opcional() -> None:
    schema = app.openapi()
    ejemplar = schema["components"]["schemas"]["EjemplarOut"]
    assert "ubicacion" in ejemplar["properties"]
    assert "ubicacion" not in ejemplar.get("required", [])


def test_search_envia_criterios_de_orden_estables() -> None:
    esperados = {
        "anio_desc": ["anio:desc", "titulo:asc"],
        "anio_asc": ["anio:asc", "titulo:asc"],
        "duracion_asc": ["duracion_min:asc", "titulo:asc"],
    }
    for sort, criterios in esperados.items():
        search, index = _catalog_search()
        app.dependency_overrides[get_indexer] = _indexer_override(search)
        try:
            client = TestClient(app)
            response = client.get("/api/search", params={"q": "cine", "sort": sort})
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert index.options is not None
        assert index.options["sort"] == criterios


@pytest.fixture(autouse=True)
def _default_db_override():
    session = _sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    yield
    app.dependency_overrides.clear()
    session.close()


class _TwoPassIndex:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search(self, query, options):  # noqa: ANN001
        self.calls.append(dict(options))
        if options.get("distinct") == "obra_key":
            return {
                "hits": [{"id": "madrid_1", "record_id": "madrid:1"}],
                "estimatedTotalHits": 1,
                "processingTimeMs": 2,
                "facetDistribution": {},
            }
        return {
            "hits": [],
            "estimatedTotalHits": 4,
            "processingTimeMs": 3,
            "facetDistribution": {"soportes": {"DVD": 4}},
        }


def test_catalog_search_usa_distinct_y_separa_totales() -> None:
    index = _TwoPassIndex()
    search = CatalogSearch.__new__(CatalogSearch)
    search.client = object()
    search.index = index

    result = search.search("vida padre")

    assert index.calls[0]["distinct"] == "obra_key"
    assert "distinct" not in index.calls[1]
    assert index.calls[1]["hitsPerPage"] == 1
    assert result["total"] == 1
    assert result["total_ediciones"] == 4
    assert result["facets"] == {"soportes": {"DVD": 4}}


def _session_with_obra(ediciones: int = 4):
    session = _sqlite_session()
    obra = Obra(titulo_uniforme="La vida padre", anio=2022)
    session.add(obra)
    session.flush()
    for number in range(1, ediciones + 1):
        biblioteca = Biblioteca(
            fuente_id=_fuente(session).id,
            codigo=f"B{number}",
            nombre=f"Biblioteca {number}",
        )
        edicion = Edicion(
            fuente_id=_fuente(session).id,
            record_id=f"madrid:{number}",
            titn=str(number),
            titulo="La vida padre",
            titulo_uniforme="La vida padre",
            anio=2022,
            obra=obra,
            soportes=["DVD"] if number % 2 else ["Blu-ray"],
        )
        session.add_all([biblioteca, edicion])
        session.flush()
        session.add(
            Ejemplar(
                fuente_id=_fuente(session).id,
                edicion=edicion,
                biblioteca=biblioteca,
                external_key=f"k{number}",
            )
        )
    session.commit()
    return session, obra


class _ObraHitIndexer:
    def __init__(self, obra_id: int) -> None:
        self.obra_id = obra_id

    def search(self, query, **kwargs):  # noqa: ANN001, ANN003
        return {
            "query": query,
            "page": 1,
            "limit": 20,
            "total": 1,
            "total_ediciones": 4,
            "total_pages": 1,
            "took_ms": 1,
            "facets": {"soportes": {"DVD": 4}},
            "hits": [
                {
                    "id": "madrid_1",
                    "record_id": "madrid:1",
                    "fuente": "madrid",
                    "titn": "1",
                    "titulo": "La vida padre",
                    "obra_id": self.obra_id,
                    "obra_titulo": "La vida padre",
                    "ediciones_count": 1,
                    "soportes": [],
                    "bibliotecas": [],
                    "ejemplares": 0,
                }
            ],
        }


def test_search_agrega_las_ediciones_de_una_obra() -> None:
    session, obra = _session_with_obra(4)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_indexer] = lambda: _ObraHitIndexer(obra.id)
    try:
        response = TestClient(app).get("/api/search", params={"q": "vida padre"})
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["total_ediciones"] == 4
    assert len(body["hits"]) == 1
    hit = body["hits"][0]
    assert hit["obra_id"] == obra.id
    assert hit["obra_titulo"] == "La vida padre"
    assert hit["ediciones_count"] == 4
    assert hit["soportes"] == ["Blu-ray", "DVD"]
    assert hit["bibliotecas"] == [
        "Biblioteca 1",
        "Biblioteca 2",
        "Biblioteca 3",
        "Biblioteca 4",
    ]
    assert hit["ejemplares"] == 4


def test_record_incluye_las_ediciones_de_la_obra() -> None:
    session, obra = _session_with_obra(2)
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/records/madrid:1")
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert response.status_code == 200
    body = response.json()
    assert body["obra"]["id"] == obra.id
    ediciones = body["obra"]["ediciones"]
    assert [edicion["record_id"] for edicion in ediciones] == [
        "madrid:1",
        "madrid:2",
    ]
    first = ediciones[0]
    assert first["fuente"] == "madrid"
    assert first["titn"] == "1"
    assert first["soportes"] == ["DVD"]
    assert first["ejemplares"] == 1
    assert first["source_url"]


def test_openapi_incluye_campos_de_agrupacion() -> None:
    schema = app.openapi()
    search_hit = schema["components"]["schemas"]["SearchHit"]
    assert "obra_id" in search_hit["properties"]
    assert "obra_titulo" in search_hit["properties"]
    assert "ediciones_count" in search_hit["properties"]
    search_response = schema["components"]["schemas"]["SearchResponse"]
    assert "total_ediciones" in search_response["properties"]
    obra = schema["components"]["schemas"]["ObraOut"]
    assert "ediciones" in obra["properties"]
