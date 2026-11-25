from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

from mediateca_shared.constants import (
    MAX_WORKER_CONCURRENCY,
    MIN_WORKER_CONCURRENCY,
)
from sqlalchemy import delete, inspect, select
from sqlalchemy.orm import Session

from mediateca.core.config import DEFAULT_TMDB_MAX_MATCH_ATTEMPTS, settings
from mediateca.core.logging import get_logger
from mediateca.core.models import AppConfig

logger = get_logger(__name__)

FLARESOLVERR_URL_KEY = "flaresolverr_url"
TMDB_API_TOKEN_KEY = "tmdb_api_token"
TMDB_MAX_MATCH_ATTEMPTS_KEY = "tmdb_max_match_attempts"
WORKER_CONCURRENCY_KEY = "worker_concurrency"
MAX_URL_LENGTH = 2000
MIN_TOKEN_LENGTH = 10
MAX_TOKEN_LENGTH = 512
MIN_TMDB_MATCH_ATTEMPTS = 1
MAX_TMDB_MATCH_ATTEMPTS = 100
TOKEN_RE = re.compile(r"[A-Za-z0-9._-]+")


class ConfigValidationError(ValueError):
    pass


def normalize_flaresolverr_url(value: str | None) -> str | None:
    """Valida y normaliza una URL base de FlareSolverr."""
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None
    if len(candidate) > MAX_URL_LENGTH:
        raise ConfigValidationError(
            f"La URL de FlareSolverr no puede superar {MAX_URL_LENGTH} caracteres"
        )
    if any(char.isspace() for char in candidate):
        raise ConfigValidationError("La URL de FlareSolverr no puede contener espacios")

    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise ConfigValidationError("La URL de FlareSolverr debe usar http o https")
    if not parsed.hostname:
        raise ConfigValidationError("La URL de FlareSolverr debe incluir un host")
    if parsed.username or parsed.password:
        raise ConfigValidationError(
            "La URL de FlareSolverr no puede incluir credenciales"
        )
    if parsed.query or parsed.fragment:
        raise ConfigValidationError(
            "La URL de FlareSolverr no puede incluir parametros ni fragmentos"
        )
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ConfigValidationError("El puerto de FlareSolverr no es valido") from exc

    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def normalize_tmdb_api_token(value: str | None) -> str | None:
    """Valida y normaliza una API Key v3 o un Read Access Token v4 de TMDB."""
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None
    if len(candidate) < MIN_TOKEN_LENGTH or len(candidate) > MAX_TOKEN_LENGTH:
        raise ConfigValidationError(
            f"El token de TMDB debe tener entre {MIN_TOKEN_LENGTH} y {MAX_TOKEN_LENGTH} caracteres"
        )
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in candidate):
        raise ConfigValidationError(
            "El token de TMDB no puede contener espacios ni caracteres de control"
        )
    if not TOKEN_RE.fullmatch(candidate):
        raise ConfigValidationError("El token de TMDB contiene caracteres no validos")
    return candidate


def normalize_tmdb_max_match_attempts(value: str | int | None) -> int | None:
    """Valida el limite de intentos automaticos de match por edicion."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = int(text)
    except (TypeError, ValueError) as exc:
        raise ConfigValidationError(
            "El limite de intentos de TMDB debe ser un numero entero"
        ) from exc
    if not MIN_TMDB_MATCH_ATTEMPTS <= parsed <= MAX_TMDB_MATCH_ATTEMPTS:
        raise ConfigValidationError(
            "El limite de intentos de TMDB debe estar entre "
            f"{MIN_TMDB_MATCH_ATTEMPTS} y {MAX_TMDB_MATCH_ATTEMPTS}"
        )
    return parsed


def _config_table_exists(session: Session) -> bool:
    bind = session.get_bind()
    if bind is None:
        return False
    return inspect(bind).has_table(AppConfig.__tablename__)


def get_config_value(session: Session, key: str) -> str | None:
    if not _config_table_exists(session):
        return None
    value = session.scalar(select(AppConfig.value).where(AppConfig.key == key))
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def set_config_value(session: Session, key: str, value: str | None) -> None:
    text = value.strip() if value is not None else ""
    if not text:
        session.execute(delete(AppConfig).where(AppConfig.key == key))
        session.flush()
        return

    current = session.get(AppConfig, key)
    if current is None:
        session.add(AppConfig(key=key, value=text))
    else:
        current.value = text
    session.flush()


def normalize_worker_concurrency(value: str | int | None) -> int | None:
    """Valida el numero de tareas paralelas del worker."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = int(text)
    except (TypeError, ValueError) as exc:
        raise ConfigValidationError(
            "La concurrencia del worker debe ser un numero entero"
        ) from exc
    if not MIN_WORKER_CONCURRENCY <= parsed <= MAX_WORKER_CONCURRENCY:
        raise ConfigValidationError(
            f"La concurrencia del worker debe estar entre "
            f"{MIN_WORKER_CONCURRENCY} y {MAX_WORKER_CONCURRENCY}"
        )
    return parsed


def _normalize_saved(value: str) -> str | None:
    try:
        return normalize_flaresolverr_url(value)
    except ConfigValidationError:
        logger.warning("La URL de FlareSolverr persistida no es valida; se ignora")
        return None


def _normalize_saved_tmdb_token(value: str) -> str | None:
    try:
        return normalize_tmdb_api_token(value)
    except ConfigValidationError:
        logger.warning("El token de TMDB persistido no es valido; se ignora")
        return None


def _normalize_saved_tmdb_max_match_attempts(value: str) -> int | None:
    try:
        return normalize_tmdb_max_match_attempts(value)
    except ConfigValidationError:
        logger.warning(
            "El limite de intentos de TMDB persistido no es valido; se ignora"
        )
        return None


def _normalize_saved_worker_concurrency(value: str) -> int | None:
    try:
        return normalize_worker_concurrency(value)
    except ConfigValidationError:
        logger.warning("La concurrencia del worker persistida no es valida; se ignora")
        return None


def saved_worker_concurrency(session: Session) -> int | None:
    saved = get_config_value(session, WORKER_CONCURRENCY_KEY)
    if saved is None:
        return None
    return _normalize_saved_worker_concurrency(saved)


def effective_worker_concurrency(session: Session) -> int:
    saved = saved_worker_concurrency(session)
    if saved is not None:
        return saved

    try:
        configured = normalize_worker_concurrency(settings.worker_concurrency)
    except ConfigValidationError:
        logger.warning(
            "La concurrencia del worker del entorno no es valida; se usa 1"
        )
        configured = None
    return configured if configured is not None else MIN_WORKER_CONCURRENCY


def effective_tmdb_api_token(session: Session) -> str | None:
    saved = get_config_value(session, TMDB_API_TOKEN_KEY)
    if saved:
        normalized = _normalize_saved_tmdb_token(saved)
        if normalized:
            return normalized

    if not settings.tmdb_api_token:
        return None
    try:
        return normalize_tmdb_api_token(settings.tmdb_api_token)
    except ConfigValidationError:
        logger.warning("El token de TMDB de entorno no es valido; se ignora")
        return None


def saved_tmdb_max_match_attempts(session: Session) -> int | None:
    saved = get_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY)
    if saved is None:
        return None
    return _normalize_saved_tmdb_max_match_attempts(saved)


def effective_tmdb_max_match_attempts(session: Session) -> int:
    saved = saved_tmdb_max_match_attempts(session)
    if saved is not None:
        return saved

    try:
        configured = normalize_tmdb_max_match_attempts(settings.tmdb_max_match_attempts)
    except ConfigValidationError:
        logger.warning(
            "El limite de intentos de TMDB del entorno no es valido; se usa %s",
            DEFAULT_TMDB_MAX_MATCH_ATTEMPTS,
        )
        configured = None
    return configured if configured is not None else DEFAULT_TMDB_MAX_MATCH_ATTEMPTS


def effective_flaresolverr_url(session: Session) -> str | None:
    saved = get_config_value(session, FLARESOLVERR_URL_KEY)
    if saved:
        normalized = _normalize_saved(saved)
        if normalized:
            return normalized

    if not settings.flaresolverr_url:
        return None
    try:
        return normalize_flaresolverr_url(settings.flaresolverr_url)
    except ConfigValidationError:
        logger.warning("La URL de FlareSolverr de entorno no es valida; se ignora")
        return None
