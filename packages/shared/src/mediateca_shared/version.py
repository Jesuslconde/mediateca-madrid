from __future__ import annotations

SCHEMA_VERSION = "6"


class SchemaVersionError(RuntimeError):
    pass


def check_schema_version(value: str | None) -> None:
    if value != SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Version de esquema incompatible: esperada {SCHEMA_VERSION}, encontrada {value or 'ninguna'}"
        )
