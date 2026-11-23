from __future__ import annotations

import json
import logging
import sys
import time
from datetime import UTC, datetime

from mediateca.core.config import settings

STRUCTURED_FIELDS = (
    "job_id",
    "job_type",
    "fuente",
    "record_id",
    "titn",
    "doc",
    "result",
    "duration_ms",
    "error",
    "step",
    "path",
    "method",
    "status_code",
    "rows",
    "page",
    "pool_status",
    "detail",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)
    # httpx registra la URL completa; con la API Key v3 de TMDB incluiria el token.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def elapsed_ms(started: float) -> float:
    """Milisegundos transcurridos desde un instante de time.monotonic()."""
    return round((time.monotonic() - started) * 1000, 2)
