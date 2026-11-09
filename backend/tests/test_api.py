from __future__ import annotations

from fastapi.testclient import TestClient

from mediateca.api.deps import get_indexer
from mediateca.api.main import app


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
