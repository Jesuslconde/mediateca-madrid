from __future__ import annotations

from fastapi.testclient import TestClient
from mediateca_shared.db import Base
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, Obra
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.api.aggregation import aggregate_hits
from mediateca.api.deps import get_db, get_indexer
from mediateca.api.main import app
from mediateca.catalog.search import CatalogSearch


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
    session.flush()
    session.info["fuente"] = fuente
    return session


def _obra_con_ediciones(session, n=4):
    fuente = session.info["fuente"]
    obra = Obra(titulo_uniforme="La vida padre", anio=2022)
    session.add(obra)
    session.flush()
    biblioteca = Biblioteca(fuente_id=fuente.id, codigo="B1", nombre="Central")
    session.add(biblioteca)
    session.flush()
    ediciones = []
    for i in range(n):
        soporte = "DVD" if i % 2 == 0 else "Blu-ray"
        edicion = Edicion(
            fuente_id=fuente.id,
            record_id=f"madrid:{1000 + i}",
            titn=str(1000 + i),
            titulo=f"La vida padre {i}",
            titulo_uniforme="La vida padre",
            anio=2022,
            soportes=[soporte],
            obra=obra,
        )
        session.add(edicion)
        session.flush()
        session.add(
            Ejemplar(
                fuente_id=fuente.id,
                edicion=edicion,
                biblioteca=biblioteca,
                external_key=f"k{i}",
                soporte=soporte,
            )
        )
        ediciones.append(edicion)
    session.commit()
    return obra, ediciones


def test_aggregate_hits_une_soportes_y_ejemplares() -> None:
    session = _sqlite_session()
    obra, _ediciones = _obra_con_ediciones(session, 4)

    hits = [
        {
            "id": "madrid_1000",
            "record_id": "madrid:1000",
            "titn": "1000",
            "titulo": "La vida padre 0",
            "obra_id": obra.id,
            "obra_key": f"obra:{obra.id}",
            "obra_titulo": "La vida padre",
            "soportes": ["DVD"],
            "bibliotecas": ["Central"],
            "ejemplares": 1,
            "anio": 2022,
        }
    ]

    result = aggregate_hits(session, hits)

    assert len(result) == 1
    hit = result[0]
    assert hit["ediciones_count"] == 4
    assert set(hit["soportes"]) == {"DVD", "Blu-ray"}
    assert hit["ejemplares"] == 4
    assert hit["bibliotecas"] == ["Central"]


def test_aggregate_hits_sin_obra_cuenta_una_edicion() -> None:
    session = _sqlite_session()
    hits = [{"id": "madrid_1", "record_id": "madrid:1", "titn": "1", "titulo": "X"}]
    result = aggregate_hits(session, hits)
    assert result[0]["ediciones_count"] == 1


class _RecordingIndex:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search(self, query, options):  # noqa: ANN001
        self.calls.append(dict(options))
        return {
            "hits": [],
            "totalHits": 0,
            "processingTimeMs": 0,
            "facetDistribution": {},
        }


def test_search_envia_distinct_y_consulta_de_facetas() -> None:
    index = _RecordingIndex()
    search = CatalogSearch.__new__(CatalogSearch)
    search.client = object()
    search.index = index
    session = _sqlite_session()
    app.dependency_overrides[get_indexer] = lambda: search
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"q": "cine"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(index.calls) == 2
    hits_call, facets_call = index.calls
    assert hits_call.get("distinct") == "obra_key"
    assert "facets" not in hits_call
    assert "distinct" not in facets_call
    assert "facets" in facets_call


def test_search_devuelve_total_ediciones() -> None:
    class _Index:
        def search(self, query, options):  # noqa: ANN001
            if "distinct" in options:
                return {
                    "hits": [],
                    "totalHits": 3,
                    "processingTimeMs": 0,
                    "facetDistribution": {},
                }
            return {
                "hits": [],
                "totalHits": 8,
                "processingTimeMs": 0,
                "facetDistribution": {"soporte": {"DVD": 8}},
            }

    search = CatalogSearch.__new__(CatalogSearch)
    search.client = object()
    search.index = _Index()
    session = _sqlite_session()
    app.dependency_overrides[get_indexer] = lambda: search
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/search", params={"q": "cine"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["total_ediciones"] == 8
    assert body["facets"] == {"soporte": {"DVD": 8}}


def test_record_incluye_ediciones_hermanas() -> None:
    session = _sqlite_session()
    obra, ediciones = _obra_con_ediciones(session, 3)
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/records/1000")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["obra"]["id"] == obra.id
    hermanas = body["obra"]["ediciones"]
    assert {h["record_id"] for h in hermanas} == {
        "madrid:1000",
        "madrid:1001",
        "madrid:1002",
    }
    primera = hermanas[0]
    assert primera["fuente"] == "madrid"
    assert primera["titn"] == "1000"
    assert primera["ejemplares"] == 1
    assert "source_url" in primera


def test_record_sin_obra_no_tiene_ediciones() -> None:
    session = _sqlite_session()
    edicion = Edicion(
        fuente_id=session.info["fuente"].id,
        record_id="madrid:1",
        titn="1",
        titulo="Abejas",
    )
    session.add(edicion)
    session.commit()
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/records/1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["obra"] is None
