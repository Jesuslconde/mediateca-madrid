from __future__ import annotations

from contextlib import contextmanager

from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Obra
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

import mediateca.cli as cli_module
from mediateca.catalog.title_backfill import backfill_titles, title_from_marc
from mediateca.core.db import Base


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _edicion(
    session,
    titn: str,
    titulo: str,
    *,
    titulo_uniforme: str | None = None,
    marc: dict | None = None,
):
    obra = Obra(titulo_uniforme=titulo_uniforme or titulo, anio=2024)
    session.add(obra)
    edicion = Edicion(
        titn=titn,
        titulo=titulo,
        titulo_uniforme=titulo_uniforme,
        obra=obra,
        marc=marc or {},
    )
    session.add(edicion)
    biblioteca = Biblioteca(codigo=f"B{titn}", nombre="Biblioteca de prueba")
    session.add(biblioteca)
    session.flush()
    session.add(
        Ejemplar(
            edicion_id=edicion.id,
            biblioteca_id=biblioteca.id,
            external_key=f"E{titn}",
            soporte="DVD",
        )
    )
    session.commit()
    return edicion, obra


def test_title_from_marc_prioriza_titulo_propio() -> None:
    assert (
        title_from_marc(
            {"T245ab": ["Historia : legislación /"], "T245": "Historia / autor"},
            None,
        )
        == "Historia : legislación"
    )
    assert title_from_marc({"T245": "Alfredo /Marcos Ordóñez"}, None) == "Alfredo"
    assert title_from_marc({}, "La abuela /") == "La abuela"


def test_backfill_no_toca_obras_ni_ejemplares() -> None:
    session = _session()
    edicion, obra = _edicion(
        session,
        "1",
        "Historia cinematográfica de la Unión Europea :",
        titulo_uniforme=(
            "Historia cinematográfica de la Unión Europea "
            "(Película cinematográfica) /"
        ),
        marc={
            "T245ab": (
                "Historia cinematográfica de la Unión Europea : "
                "legislación cinematográfica europea /"
            ),
            "ntitl": "Historia cinematográfica de la Unión Europea :",
        },
    )
    obras_antes = session.scalar(select(func.count(Obra.id)))
    ejemplares_antes = session.scalar(select(func.count(Ejemplar.id)))
    obra_uniforme_antes = obra.titulo_uniforme

    dry_run = backfill_titles(session)
    session.refresh(edicion)

    assert dry_run.changed == 1
    assert edicion.titulo == "Historia cinematográfica de la Unión Europea :"

    aplicado = backfill_titles(session, apply=True)
    session.commit()
    session.refresh(edicion)
    session.refresh(obra)

    assert aplicado.changed == 1
    assert edicion.titulo == (
        "Historia cinematográfica de la Unión Europea : "
        "legislación cinematográfica europea"
    )
    assert edicion.titulo_uniforme == (
        "Historia cinematográfica de la Unión Europea (Película cinematográfica)"
    )
    assert obra.titulo_uniforme == obra_uniforme_antes
    assert session.scalar(select(func.count(Obra.id))) == obras_antes
    assert session.scalar(select(func.count(Ejemplar.id))) == ejemplares_antes


def test_backfill_es_idempotente() -> None:
    session = _session()
    _edicion(session, "1", "La abuela /", marc={"ntitl": "La abuela /"})

    primero = backfill_titles(session, apply=True)
    session.commit()
    segundo = backfill_titles(session, apply=True)
    session.commit()

    assert primero.changed == 1
    assert segundo.changed == 0


def test_cli_reindexa_solo_los_titn_cambiados(monkeypatch) -> None:
    session = _session()
    _edicion(session, "1", "La abuela /", marc={"ntitl": "La abuela /"})
    _edicion(session, "2", "Un amor", marc={"ntitl": "Un amor"})
    capturados: list[str] = []

    class FakeIndexer:
        def index_titns(self, session, titns):  # noqa: ANN001
            capturados.extend(titns)
            return len(titns)

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "MeiliIndexer", FakeIndexer)

    resultado = CliRunner().invoke(
        cli_module.app, ["normalize-titles", "--apply", "--reindex"]
    )

    assert resultado.exit_code == 0
    assert capturados == ["1"]


def test_cli_reindex_sin_apply_no_indexa(monkeypatch) -> None:
    session = _session()
    _edicion(session, "1", "La abuela /", marc={"ntitl": "La abuela /"})
    capturados: list[str] = []

    class FakeIndexer:
        def index_titns(self, session, titns):  # noqa: ANN001
            capturados.extend(titns)
            return len(titns)

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "MeiliIndexer", FakeIndexer)

    resultado = CliRunner().invoke(cli_module.app, ["normalize-titles", "--reindex"])

    assert resultado.exit_code == 0
    assert capturados == []
