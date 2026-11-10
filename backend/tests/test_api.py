from __future__ import annotations

from fastapi.testclient import TestClient

from mediateca.api.deps import get_indexer
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
