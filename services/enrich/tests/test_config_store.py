from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mediateca.core.config import Settings, settings
from mediateca.core.config_store import (
    FLARESOLVERR_URL_KEY,
    TMDB_API_TOKEN_KEY,
    TMDB_MAX_MATCH_ATTEMPTS_KEY,
    WORKER_CONCURRENCY_KEY,
    ConfigValidationError,
    effective_flaresolverr_url,
    effective_tmdb_api_token,
    effective_tmdb_max_match_attempts,
    effective_worker_concurrency,
    get_config_value,
    normalize_flaresolverr_url,
    normalize_tmdb_api_token,
    normalize_tmdb_max_match_attempts,
    normalize_worker_concurrency,
    saved_tmdb_max_match_attempts,
    saved_worker_concurrency,
    set_config_value,
)
from mediateca.core.db import Base
from mediateca.core.models import AppConfig  # noqa: F401  (registra la tabla)

ROOT = Path(__file__).resolve().parents[1]


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)(), engine


def test_el_modelo_crea_la_tabla_app_config() -> None:
    _, engine = _session()

    assert "app_config" in Base.metadata.tables
    assert inspect(engine).has_table("app_config")


def test_la_tabla_ausente_no_rompe_la_lectura(monkeypatch) -> None:
    session, engine = _session()
    AppConfig.__table__.drop(engine)
    monkeypatch.setattr(settings, "flaresolverr_url", "http://env:8191")

    assert get_config_value(session, FLARESOLVERR_URL_KEY) is None
    assert effective_flaresolverr_url(session) == "http://env:8191"


def test_normaliza_urls_validas() -> None:
    assert normalize_flaresolverr_url(" http://localhost:8191/ ") == (
        "http://localhost:8191"
    )
    assert normalize_flaresolverr_url("https://flare.example/base/") == (
        "https://flare.example/base"
    )
    assert normalize_flaresolverr_url("") is None
    assert normalize_flaresolverr_url(None) is None


@pytest.mark.parametrize(
    "value",
    [
        "ftp://localhost:8191",
        "localhost:8191",
        "http://user:password@localhost:8191",
        "http://localhost:8191/?token=1",
        "http://localhost:8191/#fragmento",
        "http://",
        "http://localhost:abc",
        "http://local host:8191",
        "http://localhost:8191/" + "a" * 2000,
    ],
)
def test_rechaza_urls_invalidas(value: str) -> None:
    with pytest.raises(ConfigValidationError):
        normalize_flaresolverr_url(value)


def test_lee_escribe_y_borra_la_configuracion() -> None:
    session, _ = _session()

    assert get_config_value(session, FLARESOLVERR_URL_KEY) is None

    set_config_value(session, FLARESOLVERR_URL_KEY, "http://db:8191/")
    session.commit()
    assert get_config_value(session, FLARESOLVERR_URL_KEY) == "http://db:8191/"

    set_config_value(session, FLARESOLVERR_URL_KEY, "   ")
    session.commit()
    assert get_config_value(session, FLARESOLVERR_URL_KEY) is None


def test_la_configuracion_persistida_prevalece_sobre_el_entorno(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "flaresolverr_url", "http://env:8191/")

    set_config_value(session, FLARESOLVERR_URL_KEY, "http://db:8191/")
    session.commit()

    assert effective_flaresolverr_url(session) == "http://db:8191"

    set_config_value(session, FLARESOLVERR_URL_KEY, None)
    session.commit()
    assert effective_flaresolverr_url(session) == "http://env:8191"

    monkeypatch.setattr(settings, "flaresolverr_url", None)
    assert effective_flaresolverr_url(session) is None


def test_ignora_configuracion_persistida_invalida(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "flaresolverr_url", "http://env:8191")

    set_config_value(session, FLARESOLVERR_URL_KEY, "ftp://invalido")
    session.commit()

    assert effective_flaresolverr_url(session) == "http://env:8191"


def test_settings_flaresolverr_por_defecto_y_entorno(monkeypatch) -> None:
    monkeypatch.delenv("MEDIATECA_FLARESOLVERR_URL", raising=False)
    monkeypatch.delenv("MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS", raising=False)

    defaults = Settings(_env_file=None)
    assert defaults.flaresolverr_url is None
    assert defaults.flaresolverr_max_timeout_ms == 60000

    monkeypatch.setenv("MEDIATECA_FLARESOLVERR_URL", "http://flare:8191")
    monkeypatch.setenv("MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS", "15000")

    configured = Settings(_env_file=None)
    assert configured.flaresolverr_url == "http://flare:8191"
    assert configured.flaresolverr_max_timeout_ms == 15000


def test_env_example_documenta_las_variables_de_flaresolverr() -> None:
    env_example = ROOT / ".env.example"
    if not env_example.exists():
        env_example = ROOT.parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "MEDIATECA_FLARESOLVERR_URL=" in content
    assert "MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS=60000" in content


def test_normaliza_tokens_tmdb_validos() -> None:
    v3 = "0123456789abcdef0123456789abcdef"
    v4 = "eyJhbGciOiJIUzI1NiJ9.payload.signature"
    assert normalize_tmdb_api_token(f" {v3} ") == v3
    assert normalize_tmdb_api_token(v4) == v4
    assert normalize_tmdb_api_token("") is None
    assert normalize_tmdb_api_token(None) is None


@pytest.mark.parametrize(
    "value",
    [
        "corto",
        "token con espacios",
        "token\ncon\ncontrol",
        "token con ñ",
        "a" * 513,
    ],
)
def test_rechaza_tokens_tmdb_invalidos(value: str) -> None:
    with pytest.raises(ConfigValidationError):
        normalize_tmdb_api_token(value)


def test_el_token_tmdb_persistido_prevalece_sobre_el_entorno(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "tmdb_api_token", "env-token-123456")

    set_config_value(session, TMDB_API_TOKEN_KEY, "db-token-123456")
    session.commit()
    assert effective_tmdb_api_token(session) == "db-token-123456"

    set_config_value(session, TMDB_API_TOKEN_KEY, None)
    session.commit()
    assert effective_tmdb_api_token(session) == "env-token-123456"

    monkeypatch.setattr(settings, "tmdb_api_token", None)
    assert effective_tmdb_api_token(session) is None


def test_ignora_token_tmdb_persistido_invalido(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "tmdb_api_token", "env-token-123456")

    set_config_value(session, TMDB_API_TOKEN_KEY, "token con espacios")
    session.commit()

    assert effective_tmdb_api_token(session) == "env-token-123456"


def test_env_example_documenta_las_variables_de_tmdb() -> None:
    env_example = ROOT / ".env.example"
    if not env_example.exists():
        env_example = ROOT.parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "MEDIATECA_TMDB_API_TOKEN=" in content
    assert "MEDIATECA_TMDB_LANGUAGE=es-ES" in content
    assert "MEDIATECA_TMDB_DELAY=0.25" in content
    assert "MEDIATECA_TMDB_TIMEOUT=10" in content
    assert "MEDIATECA_TMDB_MAX_RETRIES=3" in content
    assert "MEDIATECA_TMDB_MAX_MATCH_ATTEMPTS=5" in content
    assert "MEDIATECA_WORKER_CONCURRENCY=1" in content


def test_normaliza_el_limite_de_intentos_de_tmdb() -> None:
    assert normalize_tmdb_max_match_attempts(" 3 ") == 3
    assert normalize_tmdb_max_match_attempts(1) == 1
    assert normalize_tmdb_max_match_attempts(100) == 100
    assert normalize_tmdb_max_match_attempts("") is None
    assert normalize_tmdb_max_match_attempts(None) is None


@pytest.mark.parametrize("value", ["0", "101", "-1", "muchos"])
def test_rechaza_limites_de_intentos_de_tmdb_invalidos(value: str) -> None:
    with pytest.raises(ConfigValidationError):
        normalize_tmdb_max_match_attempts(value)


def test_el_limite_de_tmdb_guardado_prevalece_sobre_el_entorno(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "tmdb_max_match_attempts", 4)

    assert effective_tmdb_max_match_attempts(session) == 4

    set_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY, "7")
    session.commit()
    assert saved_tmdb_max_match_attempts(session) == 7
    assert effective_tmdb_max_match_attempts(session) == 7

    set_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY, None)
    session.commit()
    assert saved_tmdb_max_match_attempts(session) is None
    assert effective_tmdb_max_match_attempts(session) == 4


def test_ignora_limite_de_tmdb_persistido_invalido(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "tmdb_max_match_attempts", 4)

    set_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY, "101")
    session.commit()

    assert saved_tmdb_max_match_attempts(session) is None
    assert effective_tmdb_max_match_attempts(session) == 4


def test_limite_de_tmdb_de_entorno_invalido_usa_cinco(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "tmdb_max_match_attempts", 0)

    assert effective_tmdb_max_match_attempts(session) == 5


def test_normaliza_concurrencia_del_worker() -> None:
    assert normalize_worker_concurrency("3") == 3
    assert normalize_worker_concurrency(1) == 1
    assert normalize_worker_concurrency("") is None
    assert normalize_worker_concurrency(None) is None


@pytest.mark.parametrize("value", ["0", "6", "-1", "muchos"])
def test_rechaza_concurrencia_invalida(value: str) -> None:
    with pytest.raises(ConfigValidationError):
        normalize_worker_concurrency(value)


def test_la_concurrencia_guardada_prevalece_sobre_el_entorno(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "worker_concurrency", 2)

    assert effective_worker_concurrency(session) == 2

    set_config_value(session, WORKER_CONCURRENCY_KEY, "4")
    session.commit()
    assert saved_worker_concurrency(session) == 4
    assert effective_worker_concurrency(session) == 4

    set_config_value(session, WORKER_CONCURRENCY_KEY, None)
    session.commit()
    assert saved_worker_concurrency(session) is None
    assert effective_worker_concurrency(session) == 2


def test_ignora_concurrencia_persistida_invalida(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "worker_concurrency", 2)

    set_config_value(session, WORKER_CONCURRENCY_KEY, "99")
    session.commit()

    assert saved_worker_concurrency(session) is None
    assert effective_worker_concurrency(session) == 2


def test_concurrencia_de_entorno_invalida_usa_uno(monkeypatch) -> None:
    session, _ = _session()
    monkeypatch.setattr(settings, "worker_concurrency", 0)

    assert effective_worker_concurrency(session) == 1
