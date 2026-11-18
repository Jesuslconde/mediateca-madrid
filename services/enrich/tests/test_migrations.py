from __future__ import annotations

import os
import uuid
from pathlib import Path

import mediateca_shared.models  # noqa: F401  (registra las tablas)
import pytest
from sqlalchemy import create_engine

from mediateca.core.db import Base

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _database_url() -> str | None:
    return os.environ.get("MEDIATECA_TEST_DATABASE_URL")


@pytest.fixture()
def pg_connection():
    url = _database_url()
    if not url:
        pytest.skip("MEDIATECA_TEST_DATABASE_URL no esta definida")
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    schema = f"migracion_{uuid.uuid4().hex[:12]}"
    with engine.connect() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        conn.exec_driver_sql(f'SET search_path TO "{schema}"')
        try:
            yield conn, engine
        finally:
            conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    engine.dispose()


def _run_migrations(conn) -> None:
    for migration in sorted(MIGRATIONS_DIR.glob("migrate_*.sql")):
        conn.exec_driver_sql(migration.read_text(encoding="utf-8"))
    conn.exec_driver_sql(
        "INSERT INTO schema_meta (key, value) VALUES ('schema_version', '7') "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
    )


def test_migraciones_dos_veces_sobre_esquema_legacy(pg_connection) -> None:
    conn, _engine = pg_connection
    conn.exec_driver_sql(
        """
        CREATE TABLE schema_meta (key VARCHAR(64) PRIMARY KEY, value VARCHAR(64) NOT NULL);
        CREATE TABLE ediciones (
            id SERIAL PRIMARY KEY,
            titn VARCHAR(32) NOT NULL UNIQUE,
            titulo VARCHAR(1000) NOT NULL,
            obra_id INTEGER,
            anio INTEGER,
            idioma VARCHAR(16),
            pais VARCHAR(16),
            soporte_principal VARCHAR(32),
            source_url TEXT,
            is_stub BOOLEAN NOT NULL DEFAULT false,
            discovery_seen_at TIMESTAMP WITH TIME ZONE,
            detail_fetched_at TIMESTAMP WITH TIME ZONE,
            tmdb_enriched_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        CREATE TABLE bibliotecas (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(64) NOT NULL UNIQUE,
            nombre VARCHAR(500) NOT NULL,
            municipio VARCHAR(250),
            direccion TEXT,
            codigo_postal VARCHAR(5),
            latitud DOUBLE PRECISION,
            longitud DOUBLE PRECISION
        );
        CREATE TABLE sucursales (
            id SERIAL PRIMARY KEY,
            biblioteca_id INTEGER NOT NULL REFERENCES bibliotecas (id),
            codigo VARCHAR(64) NOT NULL UNIQUE,
            nombre VARCHAR(500) NOT NULL,
            municipio VARCHAR(250),
            direccion TEXT,
            codigo_postal VARCHAR(5),
            latitud DOUBLE PRECISION,
            longitud DOUBLE PRECISION,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        CREATE TABLE ejemplares (
            id SERIAL PRIMARY KEY,
            edicion_id INTEGER NOT NULL REFERENCES ediciones (id),
            biblioteca_id INTEGER NOT NULL REFERENCES bibliotecas (id),
            external_key VARCHAR(64) NOT NULL,
            CONSTRAINT uq_ejemplar_external_key UNIQUE (external_key)
        );
        CREATE TABLE harvest_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(32) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            cursor_doc INTEGER,
            cursor_titn VARCHAR(32),
            batch_size INTEGER NOT NULL DEFAULT 5000,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            stats JSON NOT NULL DEFAULT '{}'::json,
            error TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            started_at TIMESTAMP WITH TIME ZONE,
            finished_at TIMESTAMP WITH TIME ZONE,
            heartbeat_at TIMESTAMP WITH TIME ZONE
        );
        CREATE TABLE listas (
            id UUID PRIMARY KEY,
            token_hash VARCHAR(64) NOT NULL,
            titulo VARCHAR(80) NOT NULL DEFAULT 'Mi lista',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        CREATE TABLE lista_items (
            lista_id UUID NOT NULL REFERENCES listas (id) ON DELETE CASCADE,
            titn VARCHAR(32) NOT NULL,
            titulo_snapshot VARCHAR(1000) NOT NULL,
            added_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            PRIMARY KEY (lista_id, titn)
        );
        INSERT INTO ediciones (titn, titulo) VALUES ('2101557', 'Abejas');
        INSERT INTO bibliotecas (codigo, nombre) VALUES ('RBMALC', 'Biblioteca');
        INSERT INTO sucursales (biblioteca_id, codigo, nombre)
            VALUES (1, 'BMALC1', 'Sucursal');
        INSERT INTO ejemplares (edicion_id, biblioteca_id, external_key)
            VALUES (1, 1, 'k1');
        INSERT INTO listas (id, token_hash, expires_at)
            VALUES ('00000000-0000-0000-0000-000000000001', 'hash', now() + interval '1 day');
        INSERT INTO lista_items (lista_id, titn, titulo_snapshot)
            VALUES ('00000000-0000-0000-0000-000000000001', '2101557', 'Abejas');
        """
    )

    _run_migrations(conn)
    _run_migrations(conn)

    assert conn.exec_driver_sql(
        "SELECT count(*) FROM fuentes WHERE codigo = 'madrid'"
    ).scalar_one() == 1
    assert conn.exec_driver_sql(
        "SELECT record_id FROM ediciones WHERE titn = '2101557'"
    ).scalar_one() == "madrid:2101557"
    assert conn.exec_driver_sql(
        "SELECT fuente_id FROM ejemplares WHERE external_key = 'k1'"
    ).scalar_one() is not None
    assert conn.exec_driver_sql(
        "SELECT record_id FROM lista_items"
    ).scalar_one() == "madrid:2101557"
    assert conn.exec_driver_sql(
        "SELECT value FROM schema_meta WHERE key = 'schema_version'"
    ).scalar_one() == "7"


def test_migraciones_sobre_esquema_nuevo_son_idempotentes(pg_connection) -> None:
    conn, _engine = pg_connection
    Base.metadata.create_all(conn)

    _run_migrations(conn)
    _run_migrations(conn)

    assert conn.exec_driver_sql(
        "SELECT count(*) FROM fuentes WHERE codigo = 'madrid'"
    ).scalar_one() == 1
