from __future__ import annotations

from fastapi.testclient import TestClient
from mediateca_shared.models import Edicion

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
        'bibliotecas = "Biblioteca Regional de Madrid Joaquín Leguina"'
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
        'bibliotecas = "Biblioteca Regional de Madrid Joaquín Leguina"'
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


def _edicion(paises_origen: list[str]) -> Edicion:
    edicion = Edicion(
        titn="2101557",
        titulo="Abejas",
        paises_origen=paises_origen,
    )
    edicion.materias = []
    edicion.personas = []
    edicion.enlaces = []
    edicion.ejemplares = []
    edicion.obra = None
    edicion.updated_at = None
    return edicion


def _get_record(paises_origen: list[str]):
    app.dependency_overrides[get_db] = lambda: _FakeSession(_edicion(paises_origen))
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
