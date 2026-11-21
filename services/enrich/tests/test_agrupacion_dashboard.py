from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import unquote_plus

from fastapi.testclient import TestClient
from mediateca_shared.models import Edicion, Obra
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import mediateca.dashboard.app as dashboard_module
from mediateca.catalog.jobs import create_stub
from mediateca.core.db import Base
from mediateca.dashboard.agrupacion_queries import (
    AgrupacionFilter,
    agrupacion_rows,
    agrupacion_summary,
    agrupacion_total,
    obras_candidatas,
)


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _override_session(session):
    def dependency():
        yield session

    return dependency


def _client_for(session) -> TestClient:
    dashboard_module.app.dependency_overrides[dashboard_module.get_session] = (
        _override_session(session)
    )
    return TestClient(dashboard_module.app)


def _clear_overrides() -> None:
    dashboard_module.app.dependency_overrides.clear()


class _FakeIndexer:
    def __init__(self) -> None:
        self.indexed: list[str] = []

    def index_titns(self, session, record_ids):  # noqa: ANN001
        self.indexed.extend(record_ids)
        return len(record_ids)


def _edicion(
    session,
    titn,
    *,
    obra: Obra | None = None,
    obra_manual: bool = False,
    soporte: str | None = None,
    titulo: str | None = None,
) -> Edicion:
    edicion = create_stub(session, titn)
    edicion.titulo = titulo or f"Titulo {titn}"
    edicion.obra = obra
    edicion.obra_manual = obra_manual
    edicion.soporte_principal = soporte
    session.flush()
    return edicion


def test_resumen_de_agrupacion() -> None:
    session = _session()
    obra = Obra(titulo_uniforme="Manual", anio=2023)
    obra.manual = True
    session.add(obra)
    session.flush()
    _edicion(session, "1", obra=obra, obra_manual=True)
    _edicion(session, "2", obra=obra, obra_manual=False)
    _edicion(session, "3", obra=None)
    session.commit()

    summary = agrupacion_summary(session)

    assert summary.total == 3
    assert summary.manual == 1
    assert summary.automatica == 1
    assert summary.sin_obra == 1


def test_filtro_por_estado_y_texto() -> None:
    session = _session()
    obra = Obra(titulo_uniforme="La vida padre", anio=2022)
    session.add(obra)
    session.flush()
    _edicion(session, "1", obra=obra, obra_manual=True, titulo="La vida padre")
    _edicion(session, "2", obra=obra, obra_manual=False, titulo="La vida padre")
    _edicion(session, "3", obra=None, titulo="Otro titulo")
    session.commit()

    assert [e.titn for e in agrupacion_rows(session, AgrupacionFilter(estado="manual"))] == ["1"]
    assert [e.titn for e in agrupacion_rows(session, AgrupacionFilter(estado="sin_obra"))] == ["3"]
    assert [e.titn for e in agrupacion_rows(session, AgrupacionFilter(texto="vida"))] == ["1", "2"]
    assert agrupacion_total(session, AgrupacionFilter(estado="automatica")) == 1


def test_obras_candidatas_ordenadas() -> None:
    session = _session()
    a = Obra(titulo_uniforme="Beta", anio=2020)
    b = Obra(titulo_uniforme="Alfa", anio=2021)
    session.add_all([a, b])
    session.commit()

    assert [obra.titulo_uniforme for obra in obras_candidatas(session)] == ["Alfa", "Beta"]


def test_agrupacion_responde_y_muestra_ediciones(monkeypatch, tmp_path) -> None:
    session = _session()
    obra = Obra(titulo_uniforme="La vida padre", anio=2022)
    session.add(obra)
    session.flush()
    _edicion(session, "1", obra=obra, obra_manual=True, titulo="La vida padre")
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", None)

    client = _client_for(session)
    try:
        response = client.get("/agrupacion")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert "La vida padre" in response.text
    assert 'name="record_id"' in response.text
    assert "manual" in response.text


def test_agrupacion_es_de_solo_lectura(monkeypatch, tmp_path) -> None:
    session = _session()
    _edicion(session, "1")
    session.commit()
    before = session.scalar(select(func.count(Edicion.id)))

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    client = _client_for(session)
    try:
        for _ in range(3):
            assert client.get("/agrupacion").status_code == 200
    finally:
        _clear_overrides()

    assert session.scalar(select(func.count(Edicion.id))) == before


def test_post_agrupar_en_obra_existente(monkeypatch, tmp_path) -> None:
    session = _session()
    dest = Obra(titulo_uniforme="La vida padre", anio=2023)
    session.add(dest)
    session.flush()
    e1 = _edicion(session, "1", titulo="La vida padre")
    e2 = _edicion(session, "2", titulo="La vida padre")
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", None)
    monkeypatch.setattr(dashboard_module, "MeiliIndexer", _FakeIndexer)

    client = _client_for(session)
    try:
        response = client.post(
            "/agrupacion/agrupar",
            data={"record_id": [e1.record_id, e2.record_id], "obra_id": str(dest.id)},
            follow_redirects=False,
        )
    finally:
        _clear_overrides()

    assert response.status_code == 303
    assert response.headers["location"].startswith("/agrupacion?message=")
    assert e1.obra_id == dest.id
    assert e2.obra_id == dest.id
    assert e1.obra_manual is True
    assert e2.obra_manual is True
    assert dest.manual is True


def test_post_agrupar_en_obra_nueva(monkeypatch, tmp_path) -> None:
    session = _session()
    e1 = _edicion(session, "1", titulo="La vida padre")
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", None)
    monkeypatch.setattr(dashboard_module, "MeiliIndexer", _FakeIndexer)

    client = _client_for(session)
    try:
        response = client.post(
            "/agrupacion/agrupar-nueva",
            data={
                "record_id": [e1.record_id],
                "titulo_uniforme": "La vida padre",
                "anio": "2022",
            },
            follow_redirects=False,
        )
    finally:
        _clear_overrides()

    assert response.status_code == 303
    obra = session.scalars(select(Obra)).one()
    assert obra.manual is True
    assert e1.obra_id == obra.id
    assert e1.obra_manual is True


def test_post_desvincular_recalcula(monkeypatch, tmp_path) -> None:
    session = _session()
    manual = Obra(titulo_uniforme="La vida padre", anio=2023)
    manual.manual = True
    session.add(manual)
    session.flush()
    e1 = _edicion(session, "1", obra=manual, obra_manual=True, titulo="La vida padre")
    e1.titulo_uniforme = "La vida padre"
    e1.anio = 2022
    e1.obra_manual_at = datetime.now(UTC)
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", None)
    monkeypatch.setattr(dashboard_module, "MeiliIndexer", _FakeIndexer)

    client = _client_for(session)
    try:
        response = client.post(
            "/agrupacion/desvincular",
            data={"record_id": [e1.record_id]},
            follow_redirects=False,
        )
    finally:
        _clear_overrides()

    assert response.status_code == 303
    assert e1.obra_manual is False
    assert e1.obra_manual_at is None


def test_post_requiere_token_de_administracion(monkeypatch, tmp_path) -> None:
    session = _session()
    e1 = _edicion(session, "1")
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", "secreto")

    client = _client_for(session)
    try:
        response = client.post(
            "/agrupacion/agrupar",
            data={"record_id": [e1.record_id], "obra_id": "1"},
            follow_redirects=False,
        )
    finally:
        _clear_overrides()

    assert response.status_code == 303
    assert "Token de administracion" in unquote_plus(response.headers["location"])
    assert e1.obra_id is None


def test_post_seleccion_invalida_sin_ediciones(monkeypatch, tmp_path) -> None:
    session = _session()
    session.commit()

    monkeypatch.setattr(dashboard_module.settings, "worker_heartbeat_file", tmp_path / "missing")
    monkeypatch.setattr(dashboard_module.settings, "dashboard_admin_token", None)

    client = _client_for(session)
    try:
        response = client.post(
            "/agrupacion/agrupar",
            data={"obra_id": "1"},
            follow_redirects=False,
        )
    finally:
        _clear_overrides()

    assert response.status_code == 303
    assert "Selecciona al menos una edicion" in unquote_plus(response.headers["location"])
