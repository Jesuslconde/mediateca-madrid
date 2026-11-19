from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

from mediateca_shared.models import Edicion, HarvestJob
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typer.testing import CliRunner

import mediateca.cli as cli_module
from mediateca.catalog.harvester import Harvester, SearchPage
from mediateca.catalog.jobs import create_stub, mark_enriched
from mediateca.catalog.tmdb import TmdbMovieDetail, TmdbSearchResult
from mediateca.core.db import Base


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_cli_discover_crea_stubs(
    monkeypatch, tmp_path, search_results_fixture
) -> None:
    session = _session()
    html = search_results_fixture.read_text(encoding="utf-8")

    class FakeOpacClient:
        def __init__(self, *args, **kwargs) -> None:
            self.delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

        def search_all(
            self,
            query: str,
            *,
            max_pages: int | None = None,
            start_doc: int | None = None,
        ):
            yield SearchPage(query=query, total=3, items=[], html=html)

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(
        cli_module,
        "Harvester",
        lambda session, **kwargs: Harvester(session, **kwargs),
    )

    result = CliRunner().invoke(
        cli_module.app, ["discover", "--max-pages", "1", "--delay", "0.1"]
    )

    assert result.exit_code == 0, result.output
    assert session.scalar(select(func.count(Edicion.id))) == 3


def test_cli_enrich_procesa_el_lote(monkeypatch, dvd_fixture) -> None:
    session = _session()
    create_stub(session, "2101557")
    session.commit()
    html = dvd_fixture.read_text(encoding="utf-8")

    class FakeOpacClient:
        def __init__(self, *args, **kwargs) -> None:
            self.delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

        def fetch_by_titn(self, titn: str) -> tuple[str, str]:
            return html, f"https://opac.example/TITN={titn}"

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app, ["enrich", "--limit", "5000", "--delay", "0.1"]
    )

    assert result.exit_code == 0, result.output
    edicion = session.scalars(select(Edicion)).one()
    assert edicion.titn == "2101557"
    assert edicion.detail_fetched_at is not None
    assert edicion.is_stub is False


def test_cli_incluye_el_comando_dashboard() -> None:
    result = CliRunner().invoke(cli_module.app, ["--help"])

    assert result.exit_code == 0
    assert "dashboard" in result.output


def test_cli_enqueue_branches_crea_el_trabajo(monkeypatch) -> None:
    session = _session()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(cli_module.app, ["enqueue-branches"])

    assert result.exit_code == 0, result.output
    job = session.scalars(select(HarvestJob)).one()
    assert job.job_type == "branches"
    assert job.status == "pending"
    assert job.stats["only_known"] is True


def test_cli_discover_usa_la_url_de_flaresolverr(monkeypatch) -> None:
    from mediateca.core.config_store import FLARESOLVERR_URL_KEY, set_config_value

    session = _session()
    set_config_value(session, FLARESOLVERR_URL_KEY, "http://db:8191")
    session.commit()

    capturado: dict = {}

    class FakeOpacClient:
        def __init__(self, *args, **kwargs) -> None:
            capturado.update(kwargs)
            self.delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

        def search_all(
            self,
            query: str,
            *,
            max_pages: int | None = None,
            start_doc: int | None = None,
        ):
            yield SearchPage(query=query, total=0, items=[], html="<html></html>")

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app, ["discover", "--max-pages", "1", "--delay", "0.1"]
    )

    assert result.exit_code == 0, result.output
    assert capturado["flaresolverr_url"] == "http://db:8191"


class _FakeTmdbClient:
    def __init__(self, *, match: bool = True) -> None:
        self.match = match
        self.calls: list[tuple[str, int | None]] = []

    def search_movie(self, query: str, *, year: int | None = None):
        self.calls.append((query, year))
        if not self.match:
            return []
        return [
            TmdbSearchResult(
                id=abs(hash(query)) % 100000,
                title=query,
                original_title=query,
                release_date=f"{year or 2020}-01-01",
                popularity=1.0,
            )
        ]

    def get_movie(self, movie_id: int):
        return TmdbMovieDetail(
            id=movie_id,
            title="Pelicula",
            original_title="Pelicula",
            release_date="2020-01-01",
            production_countries=["ES"],
            poster_path="/poster.jpg",
        )

    def close(self) -> None:
        pass


def _enriched_edition(session, titn: str, titulo: str, anio: int):
    edicion = create_stub(session, titn)
    edicion.titulo = titulo
    edicion.anio = anio
    mark_enriched(session, edicion)
    return edicion


def test_cli_tmdb_enrich_procesa_por_lotes_y_reanuda(
    monkeypatch, tmp_path
) -> None:
    session = _session()
    _enriched_edition(session, "1", "Pelicula A", 2020)
    _enriched_edition(session, "2", "Pelicula B", 2021)
    session.commit()

    class FakeOpacClient:
        delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    tmdb = _FakeTmdbClient()
    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "build_tmdb_client", lambda *args, **kwargs: tmdb)

    first = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "1", "--delay", "0", "--no-index"],
    )
    assert first.exit_code == 0, first.output
    ediciones = {
        edicion.titn: edicion for edicion in session.scalars(select(Edicion))
    }
    assert ediciones["1"].tmdb_enriched_at is not None
    assert ediciones["2"].tmdb_enriched_at is None

    second = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "10", "--delay", "0", "--no-index"],
    )
    assert second.exit_code == 0, second.output
    session.expire_all()
    ediciones = {
        edicion.titn: edicion for edicion in session.scalars(select(Edicion))
    }
    assert ediciones["1"].tmdb_enriched_at is not None
    assert ediciones["1"].tmdb_poster_url == (
        "https://image.tmdb.org/t/p/w500/poster.jpg"
    )
    assert ediciones["1"].tmdb_url is not None
    assert ediciones["2"].tmdb_enriched_at is not None


def test_cli_tmdb_enrich_completa_portadas_ya_enriquecidas(
    monkeypatch, tmp_path
) -> None:
    session = _session()
    edicion = _enriched_edition(session, "1", "Pelicula A", 2020)
    edicion.tmdb_id = 42
    edicion.tmdb_enriched_at = datetime(2025, 1, 1, tzinfo=UTC)
    session.commit()

    class FakeOpacClient:
        delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    tmdb = _FakeTmdbClient()
    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "build_tmdb_client", lambda *args, **kwargs: tmdb)

    result = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "10", "--delay", "0", "--no-index"],
    )

    assert result.exit_code == 0, result.output
    session.refresh(edicion)
    assert edicion.tmdb_poster_url == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert edicion.tmdb_url == f"https://www.themoviedb.org/movie/{edicion.tmdb_id}"
    assert tmdb.calls


def test_cli_tmdb_enrich_refresh_reactualiza_ya_sincronizadas(
    monkeypatch, tmp_path
) -> None:
    session = _session()
    edicion = _enriched_edition(session, "1", "Pelicula A", 2020)
    edicion.tmdb_id = 42
    edicion.tmdb_url = "https://www.themoviedb.org/movie/42"
    edicion.tmdb_poster_url = "https://image.tmdb.org/t/p/w500/old.jpg"
    edicion.tmdb_enriched_at = datetime(2025, 1, 1, tzinfo=UTC)
    session.commit()

    class FakeOpacClient:
        delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    sin_refresco = _FakeTmdbClient()
    monkeypatch.setattr(
        cli_module, "build_tmdb_client", lambda *args, **kwargs: sin_refresco
    )
    sin_refresco_result = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "10", "--delay", "0", "--no-index"],
    )
    assert sin_refresco_result.exit_code == 0, sin_refresco_result.output
    assert sin_refresco.calls == []

    con_refresco = _FakeTmdbClient()
    monkeypatch.setattr(
        cli_module, "build_tmdb_client", lambda *args, **kwargs: con_refresco
    )
    con_refresco_result = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "10", "--delay", "0", "--no-index", "--refresh"],
    )

    assert con_refresco_result.exit_code == 0, con_refresco_result.output
    assert con_refresco.calls
    session.refresh(edicion)
    assert edicion.tmdb_poster_url == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert edicion.tmdb_url != "https://www.themoviedb.org/movie/42"


def test_cli_tmdb_enrich_sin_token_falla_sin_modificar(monkeypatch, tmp_path) -> None:
    session = _session()
    edicion = _enriched_edition(session, "1", "Pelicula A", 2020)
    session.commit()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "build_tmdb_client", lambda *args, **kwargs: None)

    result = CliRunner().invoke(cli_module.app, ["tmdb-enrich", "--limit", "10"])

    assert result.exit_code == 1
    assert "No hay token de TMDB" in result.output
    session.refresh(edicion)
    assert edicion.tmdb_enriched_at is None


def test_cli_tmdb_enrich_indexa_los_titn_procesados(monkeypatch, tmp_path) -> None:
    session = _session()
    _enriched_edition(session, "1", "Pelicula A", 2020)
    session.commit()

    class FakeOpacClient:
        delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    class FakeIndexer:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        def index_titns(self, session, titns):  # noqa: ANN001
            self.calls.append(list(titns))
            return len(titns)

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    indexer = FakeIndexer()
    tmdb = _FakeTmdbClient()
    monkeypatch.setattr(cli_module, "OpacClient", FakeOpacClient)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module, "build_tmdb_client", lambda *args, **kwargs: tmdb)
    monkeypatch.setattr(cli_module, "MeiliIndexer", lambda: indexer)

    result = CliRunner().invoke(
        cli_module.app,
        ["tmdb-enrich", "--limit", "10", "--delay", "0"],
    )

    assert result.exit_code == 0, result.output
    assert indexer.calls == [["1"]]


def test_cli_refresh_branches_invoca_la_actualizacion(monkeypatch) -> None:
    from mediateca.catalog.directory import RefreshStats

    session = _session()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    class FakeDirectoryClient:
        def __init__(self, *args, **kwargs) -> None:
            self.delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    seen: dict[str, object] = {}

    def fake_build_client(fuente, **kwargs):  # noqa: ANN001
        return FakeDirectoryClient()

    def fake_refresh(  # noqa: ANN001
        session_arg,
        client,
        *,
        fuente=None,
        limit=None,
        max_pages=None,
        only_known=False,
        create_missing=False,
    ):
        seen["limit"] = limit
        seen["max_pages"] = max_pages
        seen["only_known"] = only_known
        seen["create_missing"] = create_missing
        return RefreshStats(
            records=2,
            with_subc=2,
            with_postal_code=2,
            with_coordinates=1,
            branches_matched=2,
        )

    monkeypatch.setattr(cli_module, "build_directory_client", fake_build_client)
    monkeypatch.setattr(cli_module, "refresh_sucursales", fake_refresh)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app,
        ["refresh-branches", "--limit", "2", "--max-pages", "1", "--delay", "0.1"],
    )

    assert result.exit_code == 0, result.output
    assert seen == {
        "limit": 2,
        "max_pages": 1,
        "only_known": True,
        "create_missing": False,
    }
    assert "Fichas leidas" in result.output


def test_cli_refresh_branches_modo_create(monkeypatch) -> None:
    from mediateca_shared.models import Fuente

    from mediateca.catalog.directory import RefreshStats

    session = _session()
    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        options={
            "directory": {
                "kind": "opendata",
                "url": "https://datos.example/all",
                "mode": "create",
            }
        },
    )
    session.add(andalucia)
    session.commit()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    class FakeDirectoryClient:
        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

    seen: dict[str, object] = {}

    def fake_build_client(fuente, **kwargs):  # noqa: ANN001
        return FakeDirectoryClient()

    def fake_refresh(  # noqa: ANN001
        session_arg,
        client,
        *,
        fuente=None,
        limit=None,
        max_pages=None,
        only_known=False,
        create_missing=False,
    ):
        seen["only_known"] = only_known
        seen["create_missing"] = create_missing
        return RefreshStats(records=2, libraries_created=1, branches_created=2)

    monkeypatch.setattr(cli_module, "build_directory_client", fake_build_client)
    monkeypatch.setattr(cli_module, "refresh_sucursales", fake_refresh)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app, ["refresh-branches", "--fuente", "andalucia", "--delay", "0"]
    )

    assert result.exit_code == 0, result.output
    assert seen == {"only_known": False, "create_missing": True}
    assert "Bibliotecas creadas" in result.output


def test_cli_worker_usa_la_concurrencia_guardada(monkeypatch) -> None:
    from mediateca.core.config_store import WORKER_CONCURRENCY_KEY, set_config_value

    session = _session()
    set_config_value(session, WORKER_CONCURRENCY_KEY, "3")
    session.commit()
    threads: list[dict] = []

    class FakeThread:
        def __init__(self, *, target, kwargs, daemon) -> None:  # noqa: ANN001
            threads.append({"target": target, "kwargs": kwargs, "daemon": daemon})

        def start(self) -> None:
            pass

        def join(self) -> None:
            pass

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module.threading, "Thread", FakeThread)

    result = CliRunner().invoke(cli_module.app, ["worker"])

    assert result.exit_code == 0, result.output
    assert len(threads) == 3
    assert "concurrencia=3" in result.output


def test_cli_worker_permite_sobreescribir_la_concurrencia(monkeypatch) -> None:
    from mediateca.core.config_store import WORKER_CONCURRENCY_KEY, set_config_value

    session = _session()
    set_config_value(session, WORKER_CONCURRENCY_KEY, "2")
    session.commit()
    threads: list[dict] = []

    class FakeThread:
        def __init__(self, *, target, kwargs, daemon) -> None:  # noqa: ANN001
            threads.append({"target": target, "kwargs": kwargs, "daemon": daemon})

        def start(self) -> None:
            pass

        def join(self) -> None:
            pass

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)
    monkeypatch.setattr(cli_module.threading, "Thread", FakeThread)

    result = CliRunner().invoke(cli_module.app, ["worker", "--concurrency", "4"])

    assert result.exit_code == 0, result.output
    assert len(threads) == 4
    assert "concurrencia=4" in result.output
    assert "origen=cli" in result.output


def test_cli_usa_el_perfil_de_andalucia_en_recoleccion_e_indexado(
    monkeypatch,
) -> None:
    from mediateca_shared.models import Fuente

    from mediateca.catalog.harvester import SearchPage

    session = _session()
    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        opac_path="/cultura/absys/abnopac/abnetcl.cgi",
        session_pattern=r"/abnetcl\.cgi/([A-Za-z0-9]+)",
        format_field="select03",
        format_value="05",
        options={},
    )
    session.add(andalucia)
    session.commit()

    capturado: list[dict] = []

    class FakeOpacClient:
        def __init__(self, *args, **kwargs) -> None:
            self.delay = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

        def search_all(self, query: str, *, max_pages=None, start_doc=None):
            yield SearchPage(query=query, total=0, items=[], html="<html></html>")

        def search(self, query: str):
            return SearchPage(query=query, total=0, items=[], html="<html></html>")

    class FakeIndexer:
        def __init__(self) -> None:
            self.calls: list[int | None] = []

        def index_editions(self, session, *, reset=False, fuente_id=None):  # noqa: ANN001
            self.calls.append(fuente_id)
            return 0

    fake_indexer = FakeIndexer()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    def fake_opac_client(fuente, **kwargs):
        capturado.append({"fuente": fuente, **kwargs})
        return FakeOpacClient()

    monkeypatch.setattr(cli_module, "_opac_client", fake_opac_client)
    monkeypatch.setattr(cli_module, "MeiliIndexer", lambda: fake_indexer)
    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    for args in (
        ["discover", "--fuente", "andalucia", "--max-pages", "1", "--delay", "0.1"],
        ["harvest", "--fuente", "andalucia", "--query", "cine", "--max-pages", "1", "--limit", "1", "--delay", "0.1"],
        ["enrich", "--fuente", "andalucia", "--limit", "1", "--delay", "0.1"],
        ["index", "--fuente", "andalucia"],
    ):
        result = CliRunner().invoke(cli_module.app, args)
        assert result.exit_code == 0, result.output

    assert capturado
    assert all(
        item["fuente"].base_url == "https://www.juntadeandalucia.es"
        for item in capturado
    )
    assert all(
        item["fuente"].opac_path == "/cultura/absys/abnopac/abnetcl.cgi"
        for item in capturado
    )
    assert all(item["fuente"].format_value == "05" for item in capturado)
    assert fake_indexer.calls == [andalucia.id]


def test_cli_enqueue_branches_sin_directorio_no_encola(monkeypatch) -> None:
    from mediateca_shared.models import Fuente

    session = _session()
    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        options={},
    )
    session.add(andalucia)
    session.commit()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app, ["enqueue-branches", "--fuente", "andalucia"]
    )

    assert result.exit_code == 0, result.output
    assert "no tiene directorio" in result.output
    assert session.scalars(select(HarvestJob)).all() == []


def test_cli_refresh_branches_sin_directorio_no_falla(monkeypatch) -> None:
    from mediateca_shared.models import Fuente

    session = _session()
    andalucia = Fuente(
        codigo="andalucia",
        nombre="Andalucía",
        base_url="https://www.juntadeandalucia.es",
        options={},
    )
    session.add(andalucia)
    session.commit()

    @contextmanager
    def fake_session_scope():
        yield session
        session.commit()

    monkeypatch.setattr(cli_module, "session_scope", fake_session_scope)

    result = CliRunner().invoke(
        cli_module.app, ["refresh-branches", "--fuente", "andalucia", "--delay", "0"]
    )

    assert result.exit_code == 0, result.output
    assert "no tiene directorio" in result.output
