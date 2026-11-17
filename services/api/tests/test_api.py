from __future__ import annotations

from fastapi.testclient import TestClient
from mediateca_shared.db import Base
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Sucursal
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
        response = client.get("/api/search", params={"biblioteca": "s:BMALC1"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert index.options is not None
    assert index.options["filter"] == (
        'detail_complete = true AND ubicaciones = "s:BMALC1"'
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
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _record_with_location(
    *,
    with_sucursal: bool = True,
    sucursal_coords: bool = True,
    biblioteca_coords: bool = True,
):
    session = _sqlite_session()
    biblioteca = Biblioteca(
        codigo="RBMALC",
        nombre="Bibliotecas Municipales Alcalá",
        municipio="Alcalá de Henares",
        codigo_postal="28801",
        latitud=40.48156 if biblioteca_coords else None,
        longitud=-3.36521 if biblioteca_coords else None,
    )
    edicion = Edicion(titn="2101557", titulo="Abejas")
    session.add_all([biblioteca, edicion])
    if with_sucursal:
        session.add(
            Sucursal(
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
    assert set(locations) == {"b:RBMALC", "s:BMALC1"}

    biblioteca = locations["b:RBMALC"]
    assert biblioteca["tipo"] == "biblioteca"
    assert biblioteca["nombre"] == "Bibliotecas Municipales Alcalá"
    assert biblioteca["biblioteca_codigo"] == "RBMALC"
    assert biblioteca["ejemplares"] == 1

    sucursal = locations["s:BMALC1"]
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
    assert [item["codigo"] for item in response.json()] == ["b:RBMALC"]


def test_locations_incluye_sucursal_sin_fila_en_sucursales() -> None:
    session = _sqlite_session()
    biblioteca = Biblioteca(
        codigo="BPM",
        nombre="MADRID. Bibliotecas Públicas",
        municipio="Madrid",
    )
    edicion = Edicion(titn="1948243", titulo="Dolor y gloria")
    ejemplar = Ejemplar(
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
    assert locations["s:BP20"]["nombre"] == "VILLA DE VALLECAS. BP Luis Martín Santos"
    assert locations["s:BP20"]["biblioteca_codigo"] == "BPM"
    assert locations["s:BP20"]["municipio"] == "Madrid"


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
