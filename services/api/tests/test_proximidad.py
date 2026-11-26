from __future__ import annotations

from fastapi.testclient import TestClient
from mediateca_shared.db import Base
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, Obra, Sucursal
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.api.deps import get_db, get_indexer
from mediateca.api.main import app
from mediateca.catalog.proximidad import nearby_location_codes, reference_point
from mediateca.catalog.search import CatalogSearch


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    session.add(Fuente(codigo="madrid", nombre="Madrid", base_url="https://opac.example"))
    session.commit()
    return session


def _seed(session):
    fuente = session.scalars(select(Fuente)).one()

    biblioteca = Biblioteca(
        fuente_id=fuente.id,
        codigo="RBMALC",
        nombre="Bibliotecas Municipales Alcala",
    )
    session.add(biblioteca)
    session.flush()

    # Sucursal con coordenadas en el centro de Madrid (dentro de 5 km).
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="BMALC1",
            nombre="Cercana",
            latitud=40.4311,
            longitud=-3.7109,
        )
    )
    # Sucursal con coordenadas lejos (fuera de 5 km).
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="BMALC2",
            nombre="Lejana",
            latitud=40.50,
            longitud=-3.70,
        )
    )
    # Sucursal sin coordenadas pero con CP 28015 (dentro de 5 km por centroide).
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="BMALC3",
            nombre="SinCoords",
            codigo_postal="28015",
        )
    )

    # Biblioteca sin sucursales dentro del radio.
    session.add(
        Biblioteca(
            fuente_id=fuente.id,
            codigo="SOLA",
            nombre="Biblioteca sola",
            latitud=40.4311,
            longitud=-3.7109,
        )
    )
    # Biblioteca sin sucursales fuera del radio.
    session.add(
        Biblioteca(
            fuente_id=fuente.id,
            codigo="LEJOS",
            nombre="Biblioteca lejos",
            latitud=40.50,
            longitud=-3.70,
        )
    )
    session.commit()
    return biblioteca


def test_reference_point_centroide() -> None:
    point = reference_point("28015")
    assert point is not None
    assert abs(point[0] - 40.43) < 0.01


def test_reference_point_desconocido() -> None:
    assert reference_point("00000") is None


def test_sucursales_dentro_del_radio() -> None:
    session = _session()
    try:
        _seed(session)
        codes = set(nearby_location_codes(session, cp="28015", radio_km=5))
    finally:
        session.close()

    assert "s:madrid:BMALC1" in codes
    assert "s:madrid:BMALC3" in codes
    assert "s:madrid:BMALC2" not in codes
    assert "b:madrid:SOLA" in codes
    assert "b:madrid:LEJOS" not in codes


def test_excluir_una_sucursal() -> None:
    session = _session()
    try:
        _seed(session)
        codes = nearby_location_codes(
            session, cp="28015", radio_km=5, excluir=["s:madrid:BMALC1"]
        )
    finally:
        session.close()

    assert "s:madrid:BMALC1" not in codes
    assert "s:madrid:BMALC3" in codes


def test_excluir_una_red_quita_sus_sucursales() -> None:
    session = _session()
    try:
        _seed(session)
        codes = nearby_location_codes(
            session, cp="28015", radio_km=5, excluir=["b:madrid:RBMALC"]
        )
    finally:
        session.close()

    assert "s:madrid:BMALC1" not in codes
    assert "s:madrid:BMALC3" not in codes
    assert "b:madrid:SOLA" in codes


def test_cp_no_resoluble_devuelve_vacio() -> None:
    session = _session()
    try:
        codes = nearby_location_codes(session, cp="00000", radio_km=5)
    finally:
        session.close()

    assert codes == []


class _FakeIndex:
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


def _search(session, params):
    index = _FakeIndex()
    search = CatalogSearch.__new__(CatalogSearch)
    search.client = object()
    search.index = index
    app.dependency_overrides[get_indexer] = lambda: search
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/search", params=params)
    finally:
        app.dependency_overrides.clear()
    return response, index


def test_search_por_radio_construye_filtro() -> None:
    session = _session()
    try:
        _seed(session)
        response, index = _search(session, {"cp": "28015", "radio_km": "5"})
    finally:
        session.close()

    assert response.status_code == 200
    assert index.options is not None
    filtro = index.options["filter"]
    assert "ubicaciones IN [" in filtro
    assert '"s:madrid:BMALC1"' in filtro
    assert '"s:madrid:BMALC3"' in filtro
    assert '"b:madrid:SOLA"' in filtro
    assert '"s:madrid:BMALC2"' not in filtro


def test_search_radio_sin_cp_devuelve_422() -> None:
    session = _session()
    try:
        response, _ = _search(session, {"radio_km": "5"})
    finally:
        session.close()

    assert response.status_code == 422


def test_search_cp_no_resoluble_devuelve_422() -> None:
    session = _session()
    try:
        response, _ = _search(session, {"cp": "00000", "radio_km": "5"})
    finally:
        session.close()

    assert response.status_code == 422


def test_search_radio_sin_cercanas_devuelve_vacio() -> None:
    session = _session()
    fuente = session.scalars(select(Fuente)).one()
    biblioteca = Biblioteca(
        fuente_id=fuente.id, codigo="RBMALC", nombre="Lejana"
    )
    session.add(biblioteca)
    session.flush()
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="X",
            nombre="Lejana",
            latitud=40.50,
            longitud=-3.70,
        )
    )
    session.commit()
    try:
        response, index = _search(session, {"cp": "28015", "radio_km": "5"})
    finally:
        session.close()

    assert response.status_code == 200
    assert index.options is None  # no llega a consultar el indice
    assert response.json()["total"] == 0
    assert response.json()["hits"] == []


def test_agregacion_por_proximidad_filtra_ejemplares() -> None:
    from mediateca.api.aggregation import aggregate_hits_by_obra

    session = _session()
    fuente = session.scalars(select(Fuente)).one()
    biblioteca = Biblioteca(
        fuente_id=fuente.id, codigo="RBMALC", nombre="Alcala"
    )
    session.add(biblioteca)
    session.flush()
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="BMALC1",
            nombre="Cercana",
            latitud=40.4311,
            longitud=-3.7109,
        )
    )
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=biblioteca.id,
            codigo="BMALC2",
            nombre="Lejana",
            latitud=40.50,
            longitud=-3.70,
        )
    )
    obra = Obra(titulo_uniforme="Prueba", anio=2020)
    edicion = Edicion(
        fuente_id=fuente.id,
        record_id="madrid:1",
        titn="1",
        titulo="Prueba",
        titulo_uniforme="Prueba",
        anio=2020,
        obra=obra,
        soportes=["DVD"],
    )
    session.add_all([obra, edicion])
    session.flush()
    session.add_all(
        [
            Ejemplar(
                fuente_id=fuente.id,
                edicion=edicion,
                biblioteca=biblioteca,
                external_key="k1",
                sucursal_codigo="BMALC1",
            ),
            Ejemplar(
                fuente_id=fuente.id,
                edicion=edicion,
                biblioteca=biblioteca,
                external_key="k2",
                sucursal_codigo="BMALC2",
            ),
        ]
    )
    session.commit()

    hits = [
        {
            "id": "madrid_1",
            "record_id": "madrid:1",
            "titulo": "Prueba",
            "obra_id": obra.id,
            "soportes": [],
            "bibliotecas": [],
            "ejemplares": 0,
        }
    ]
    try:
        kept = aggregate_hits_by_obra(
            session, hits, ubicaciones=["s:madrid:BMALC1"]
        )
    finally:
        session.close()

    assert len(kept) == 1
    assert kept[0]["ejemplares"] == 1
    assert kept[0]["bibliotecas"] == ["Alcala"]


def _session_con_ubicaciones():
    session = _session()
    fuente = session.scalars(select(Fuente)).one()

    cerca = Biblioteca(
        fuente_id=fuente.id,
        codigo="CERCANA",
        nombre="Cercana",
        latitud=40.4311,
        longitud=-3.7109,
    )
    lejos = Biblioteca(
        fuente_id=fuente.id,
        codigo="LEJANA",
        nombre="Lejana",
        latitud=40.50,
        longitud=-3.70,
    )
    session.add_all([cerca, lejos])
    session.flush()
    session.add(
        Sucursal(
            fuente_id=fuente.id,
            biblioteca_id=cerca.id,
            codigo="SUC1",
            nombre="Sucursal Cercana",
            latitud=40.4311,
            longitud=-3.7109,
        )
    )
    edicion = Edicion(
        fuente_id=fuente.id,
        record_id="madrid:1",
        titn="1",
        titulo="Prueba",
    )
    session.add(edicion)
    session.flush()
    session.add(
        Ejemplar(
            fuente_id=fuente.id,
            edicion=edicion,
            biblioteca=cerca,
            external_key="k1",
            sucursal_codigo="SUC1",
        )
    )
    session.add(
        Ejemplar(
            fuente_id=fuente.id,
            edicion=edicion,
            biblioteca=lejos,
            external_key="k2",
        )
    )
    session.commit()
    return session


def test_locations_incluye_coordenadas() -> None:
    session = _session_con_ubicaciones()
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/locations")
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert response.status_code == 200
    by_codigo = {item["codigo"]: item for item in response.json()}
    cerca = by_codigo["b:madrid:CERCANA"]
    assert cerca["latitud"] == 40.4311
    assert cerca["distancia_km"] is None


def test_locations_cercanas_ordenadas_por_distancia() -> None:
    session = _session_con_ubicaciones()
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get(
            "/api/locations", params={"cp": "28015", "radio_km": "5"}
        )
    finally:
        app.dependency_overrides.clear()
        session.close()

    assert response.status_code == 200
    codigos = [item["codigo"] for item in response.json()]
    assert set(codigos) == {"b:madrid:CERCANA", "s:madrid:SUC1"}
    assert all(item["distancia_km"] is not None for item in response.json())
    distancias = [item["distancia_km"] for item in response.json()]
    assert distancias == sorted(distancias)



