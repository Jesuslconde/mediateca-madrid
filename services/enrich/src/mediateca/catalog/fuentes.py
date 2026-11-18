from __future__ import annotations

import json

from mediateca_shared.identity import MADRID
from mediateca_shared.models import Fuente
from sqlalchemy import Connection, select
from sqlalchemy.orm import Session

from mediateca.core.config import settings

DIRECTORY_PATH = "/directorio_publicacion/i18n/comunidades"
DEFAULT_SESSION_PATTERN = r"/abnetopac/([A-Za-z0-9]+)"


class FuenteNotFound(LookupError):
    pass


class FuenteDisabled(RuntimeError):
    pass


def default_options() -> dict[str, object]:
    return {"directory_path": DIRECTORY_PATH}


def ensure_default_fuente(session: Session, codigo: str = MADRID) -> Fuente:
    fuente = session.scalars(select(Fuente).where(Fuente.codigo == codigo)).first()
    if fuente is None:
        fuente = Fuente(
            codigo=codigo,
            nombre="Madrid" if codigo == MADRID else codigo,
            adapter="absysnet",
            base_url=settings.opac_base_url,
            opac_path=settings.opac_path,
            session_pattern=DEFAULT_SESSION_PATTERN,
            format_field="select03",
            format_value="6",
            enabled=True,
            delay=settings.crawl_delay,
            captcha_policy="pause",
            options=default_options(),
        )
        session.add(fuente)
        session.flush()
    return fuente


def seed_default_fuente(conn: Connection, codigo: str = MADRID) -> None:
    """Siembra Madrid con los valores de entorno antes de aplicar la migracion."""
    conn.exec_driver_sql(
        """
        INSERT INTO fuentes (
            codigo, nombre, adapter, base_url, opac_path, session_pattern,
            format_field, format_value, enabled, delay, captcha_policy, options
        )
        VALUES (
            %(codigo)s, %(nombre)s, 'absysnet', %(base_url)s, %(opac_path)s,
            %(session_pattern)s, 'select03', '6', true, %(delay)s, 'pause',
            %(options)s::json
        )
        ON CONFLICT (codigo) DO NOTHING
        """,
        {
            "codigo": codigo,
            "nombre": "Madrid" if codigo == MADRID else codigo,
            "base_url": settings.opac_base_url,
            "opac_path": settings.opac_path,
            "session_pattern": DEFAULT_SESSION_PATTERN,
            "delay": settings.crawl_delay,
            "options": json.dumps({"directory_path": DIRECTORY_PATH}),
        },
    )


def get_fuente(session: Session, codigo: str | None = None) -> Fuente:
    code = codigo or MADRID
    fuente = session.scalars(select(Fuente).where(Fuente.codigo == code)).first()
    if fuente is None:
        raise FuenteNotFound(f"Fuente no encontrada: {code}")
    return fuente


def require_enabled_fuente(session: Session, codigo: str | None = None) -> Fuente:
    code = codigo or MADRID
    try:
        fuente = get_fuente(session, code)
    except FuenteNotFound:
        if code != MADRID:
            raise
        fuente = ensure_default_fuente(session, code)
    if not fuente.enabled:
        raise FuenteDisabled(f"La fuente {fuente.codigo} esta deshabilitada")
    return fuente


def enabled_fuentes(session: Session) -> list[Fuente]:
    return list(
        session.scalars(
            select(Fuente).where(Fuente.enabled.is_(True)).order_by(Fuente.codigo)
        )
    )


def list_fuentes(session: Session) -> list[Fuente]:
    return list(session.scalars(select(Fuente).order_by(Fuente.codigo)))
