from __future__ import annotations

import logging
import re
import sys

from mediateca.core.config import settings

_TOKEN_PATTERN = re.compile(r"(/api/lists/)[^/?#\s\"]+")


class TokenMaskFilter(logging.Filter):
    """Oculta el token de las rutas de lista en los logs de acceso."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                _TOKEN_PATTERN.sub(r"\1***", arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: _TOKEN_PATTERN.sub(r"\1***", value)
                if isinstance(value, str)
                else value
                for key, value in record.args.items()
            }
        if isinstance(record.msg, str):
            record.msg = _TOKEN_PATTERN.sub(r"\1***", record.msg)
        return True


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        stream=sys.stdout,
        force=True,
    )
    access_logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(item, TokenMaskFilter) for item in access_logger.filters):
        access_logger.addFilter(TokenMaskFilter())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
