from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    database: str
    meilisearch: str
    version: str


class SearchResponse(BaseModel):
    query: str
    page: int
    limit: int
    total: int
    total_pages: int
    took_ms: int
    facets: dict[str, dict[str, int]]
    hits: list[dict[str, Any]]


class PersonaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre: str
    rol: str


class EnlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: str
    etiqueta: str | None = None


class EjemplarOut(BaseModel):
    id: int
    biblioteca: str
    biblioteca_codigo: str
    sucursal: str | None = None
    sucursal_codigo: str | None = None
    localizacion: str | None = None
    signatura: str | None = None
    tipo_ejemplar: str | None = None
    soporte: str | None = None


class ObraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo_uniforme: str
    anio: int | None = None
    director_principal: str | None = None


class RecordDetail(BaseModel):
    titn: str
    titulo: str
    titulo_uniforme: str | None = None
    publicacion: str | None = None
    anio: int | None = None
    idioma: str | None = None
    pais: str | None = None
    duracion_min: int | None = None
    edad_recomendada: str | None = None
    sinopsis: str | None = None
    generos: list[str] = []
    materias: list[str] = []
    soportes: list[str] = []
    soporte_principal: str | None = None
    ean: str | None = None
    tipo_documento: str | None = None
    personas: list[PersonaOut] = []
    enlaces: list[EnlaceOut] = []
    ejemplares: list[EjemplarOut] = []
    obra: ObraOut | None = None
    notas: dict[str, str] = {}
    marc: dict[str, Any] = {}
    source_url: str | None = None
    updated_at: str | None = None


class LibraryOut(BaseModel):
    codigo: str
    nombre: str
    municipio: str | None = None
    ejemplares: int


class StatsResponse(BaseModel):
    ediciones: int
    ejemplares: int
    bibliotecas: int
    por_soporte: dict[str, int]
