from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from mediateca_shared.db import Base
from mediateca_shared.models import (
    Biblioteca,
    Edicion,
    Ejemplar,
    Fuente,
    HarvestJob,
    Obra,
    SchemaMeta,
    Sucursal,
)
from mediateca_shared.version import SCHEMA_VERSION, SchemaVersionError, check_schema_version


def test_modelos_se_crean_en_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    assert "ediciones" in Base.metadata.tables
    assert "fuentes" in Base.metadata.tables
    assert "harvest_jobs" in Base.metadata.tables
    assert "schema_meta" in Base.metadata.tables
    assert "sucursales" in Base.metadata.tables


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


def test_sucursal_incluye_ubicacion() -> None:
    columnas = {columna.name for columna in Sucursal.__table__.columns}
    assert "codigo" in columnas
    assert "biblioteca_id" in columnas
    assert "municipio" in columnas
    assert "direccion" in columnas
    assert "codigo_postal" in columnas
    assert "latitud" in columnas
    assert "longitud" in columnas
    assert "codigo_postal" in {columna.name for columna in Biblioteca.__table__.columns}
    assert hasattr(Ejemplar, "sucursal")


def test_esquema_version_8() -> None:
    assert SCHEMA_VERSION == "8"


def test_columnas_de_agrupacion_manual() -> None:
    columnas_edicion = {columna.name for columna in Edicion.__table__.columns}
    assert "obra_manual" in columnas_edicion
    assert "obra_manual_at" in columnas_edicion

    columnas_obra = {columna.name for columna in Obra.__table__.columns}
    assert "manual" in columnas_obra
    assert "updated_at" in columnas_obra


def test_fuente_valida_codigo() -> None:
    fuente = Fuente(codigo="madrid", nombre="Madrid", base_url="https://example.org")
    assert fuente.codigo == "madrid"
    with pytest.raises(ValueError):
        Fuente(codigo="Madrid", nombre="Madrid", base_url="https://example.org")


def test_edicion_tiene_identidad_compuesta() -> None:
    columnas = {columna.name for columna in Edicion.__table__.columns}
    assert {"fuente_id", "record_id", "titn"} <= columnas
    constraints = {constraint.name for constraint in Edicion.__table__.constraints}
    assert "uq_ediciones_fuente_titn" in constraints
    assert "uq_ediciones_record_id" in constraints


def test_esquemas_de_agrupacion_tienen_valores_por_defecto() -> None:
    from mediateca_shared.schemas import ObraOut, SearchHit, SearchResponse

    hit = SearchHit(id="madrid_1", titn="1", titulo="La vida padre")
    assert hit.obra_id is None
    assert hit.obra_titulo is None
    assert hit.ediciones_count == 1

    response = SearchResponse(
        query="",
        page=1,
        limit=20,
        total=1,
        total_pages=1,
        took_ms=0,
        facets={},
        hits=[hit],
    )
    assert response.total_ediciones == 0

    obra = ObraOut(id=1, titulo_uniforme="La vida padre")
    assert obra.ediciones == []
