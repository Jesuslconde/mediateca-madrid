from __future__ import annotations

import re

MADRID = "madrid"
FUENTE_CODIGO_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TITN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class RecordIdError(ValueError):
    """Identificador de registro con formato invalido."""


def validate_fuente_codigo(codigo: str) -> str:
    if not codigo or not FUENTE_CODIGO_RE.match(codigo):
        raise RecordIdError(
            "El codigo de fuente debe cumplir ^[a-z0-9][a-z0-9-]*$"
        )
    return codigo


def validate_titn(titn: str) -> str:
    if not titn or len(titn) > 32 or not TITN_RE.match(titn):
        raise RecordIdError("El TITN no tiene un formato valido")
    return titn


def compose_record_id(fuente: str, titn: str) -> str:
    return f"{validate_fuente_codigo(fuente)}:{validate_titn(titn)}"


def parse_record_id(value: str) -> tuple[str, str]:
    """Devuelve ``(fuente, titn)``; un TITN suelto se resuelve como Madrid."""
    raw = (value or "").strip()
    if not raw:
        raise RecordIdError("El identificador de registro esta vacio")
    if ":" in raw:
        if raw.count(":") != 1:
            raise RecordIdError("El identificador de registro tiene un formato invalido")
        fuente, titn = raw.split(":", 1)
        return validate_fuente_codigo(fuente), validate_titn(titn)
    return MADRID, validate_titn(raw)


def normalize_record_id(value: str) -> str:
    fuente, titn = parse_record_id(value)
    return compose_record_id(fuente, titn)


def record_id_fuente(value: str) -> str:
    return parse_record_id(value)[0]


def record_id_titn(value: str) -> str:
    return parse_record_id(value)[1]


def normalize_location_code(code: str, default_fuente: str = MADRID) -> str:
    """Normaliza un codigo ``b:``/``s:`` historico al formato con fuente."""
    raw = (code or "").strip()
    if not raw.startswith(("b:", "s:")):
        return raw
    prefix, _, rest = raw.partition(":")
    if not rest or ":" in rest:
        return raw
    return f"{prefix}:{default_fuente}:{rest}"
