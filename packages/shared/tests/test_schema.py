from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from mediateca_shared.db import Base
from mediateca_shared.models import Edicion, HarvestJob, SchemaMeta
from mediateca_shared.version import SCHEMA_VERSION, SchemaVersionError, check_schema_version


def test_modelos_se_crean_en_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    assert "ediciones" in Base.metadata.tables
    assert "harvest_jobs" in Base.metadata.tables
    assert "schema_meta" in Base.metadata.tables


def test_version_compatible() -> None:
    check_schema_version(SCHEMA_VERSION)


def test_version_incompatible() -> None:
    with pytest.raises(SchemaVersionError):
        check_schema_version("999")


def test_modelos_esperados() -> None:
    assert Edicion.__tablename__ == "ediciones"
    assert HarvestJob.__tablename__ == "harvest_jobs"
    assert SchemaMeta.__tablename__ == "schema_meta"


def test_edicion_incluye_campos_tmdb() -> None:
    columnas = {columna.name for columna in Edicion.__table__.columns}
    assert "paises_origen" in columnas
    assert "tmdb_id" in columnas
    assert "tmdb_poster_url" in columnas
    assert "tmdb_url" in columnas
    assert "tmdb_enriched_at" in columnas
    assert "pais" in columnas


def test_edicion_incluye_campos_de_estado() -> None:
    columnas = {columna.name for columna in Edicion.__table__.columns}
    assert "enrich_status" in columnas
    assert "enrich_attempts" in columnas
    assert "enrich_last_attempt_at" in columnas
    assert "enrich_last_error" in columnas
    assert "tmdb_status" in columnas
    assert "tmdb_attempts" in columnas
    assert "tmdb_last_attempt_at" in columnas
    assert "tmdb_last_error" in columnas


def test_esquema_version_4() -> None:
    assert SCHEMA_VERSION == "4"
