from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HealthResponse(BaseModel):
    status: str
    database: str
    meilisearch: str
    version: str


class SearchHitFormatted(BaseModel):
    model_config = ConfigDict(extra="allow")

    titulo: str | None = None
    sinopsis: str | None = None


class SearchHit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    record_id: str | None = None
    fuente: str | None = None
    fuente_nombre: str | None = None
    titn: str
    titulo: str
    titulo_uniforme: str | None = None
    publicacion: str | None = None
    anio: int | None = None
    idioma: str | None = None
    pais: str | None = None
    paises_origen: list[str] = []
    tmdb_poster_url: str | None = None
    tmdb_url: str | None = None
    duracion_min: int | None = None
    edad_recomendada: str | None = None
    sinopsis: str | None = None
    generos: list[str] = []
    materias: list[str] = []
    soportes: list[str] = []
    soporte_principal: str | None = None
    bibliotecas: list[str] = []
    ejemplares: int = 0
    directores: list[str] = []
    actores: list[str] = []
    guionistas: list[str] = []
    obra_id: int | None = None
    obra_titulo: str | None = None
    ediciones_count: int = 1
    formatted: SearchHitFormatted | None = Field(default=None, alias="_formatted")


class SearchResponse(BaseModel):
    query: str
    page: int
    limit: int
    total: int
    total_ediciones: int
    total_pages: int
    took_ms: int
    facets: dict[str, dict[str, int]]
    hits: list[SearchHit]


class PersonaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre: str
    rol: str


class EnlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: str
    etiqueta: str | None = None


class UbicacionOut(BaseModel):
    codigo_postal: str | None = Field(
        default=None, description="Codigo postal de la sucursal o biblioteca"
    )
    municipio: str | None = Field(
        default=None, description="Municipio de la sucursal o biblioteca"
    )
    latitud: float | None = Field(
        default=None, description="Latitud WGS84 cuando esta disponible"
    )
    longitud: float | None = Field(
        default=None, description="Longitud WGS84 cuando esta disponible"
    )


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
    ubicacion: UbicacionOut | None = Field(
        default=None, description="Ubicacion disponible de la sucursal o biblioteca"
    )


class ObraEdicionOut(BaseModel):
    record_id: str
    fuente: str
    titn: str
    titulo: str
    anio: int | None = None
    soportes: list[str] = []
    ean: str | None = None
    ejemplares: int = 0
    source_url: str | None = None


class ObraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo_uniforme: str
    anio: int | None = None
    director_principal: str | None = None
    ediciones: list[ObraEdicionOut] = []


class RecordDetail(BaseModel):
    record_id: str
    fuente: str
    fuente_nombre: str | None = None
    titn: str
    titulo: str
    titulo_uniforme: str | None = None
    publicacion: str | None = None
    anio: int | None = None
    idioma: str | None = None
    pais: str | None = None
    paises_origen: list[str] = []
    tmdb_poster_url: str | None = None
    tmdb_url: str | None = None
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
    fuente: str
    codigo: str
    nombre: str
    municipio: str | None = None
    ejemplares: int


class LocationOut(BaseModel):
    fuente: str
    codigo: str
    nombre: str
    tipo: Literal["biblioteca", "sucursal"]
    biblioteca_codigo: str
    biblioteca_nombre: str
    municipio: str | None = None
    ejemplares: int


class StatsResponse(BaseModel):
    ediciones: int
    ejemplares: int
    bibliotecas: int
    por_soporte: dict[str, int]


class ListaItemOut(BaseModel):
    record_id: str
    fuente: str
    titn: str
    titulo: str
    soportes: list[str] = []
    anio: int | None = None
    poster_url: str | None = None
    opac_url: str | None = None
    disponible: bool = True


class ListaOut(BaseModel):
    titulo: str
    item_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    items: list[ListaItemOut] = []


class ListaCreatedOut(BaseModel):
    token: str


class ListaItemIn(BaseModel):
    record_id: str | None = Field(default=None, min_length=1, max_length=160)
    titn: str | None = Field(default=None, min_length=1, max_length=32)

    @model_validator(mode="after")
    def _require_identity(self) -> ListaItemIn:
        if not self.record_id and not self.titn:
            raise ValueError("Se requiere record_id o titn")
        return self

    @property
    def identity(self) -> str:
        return self.record_id or self.titn or ""


class ListaRenameIn(BaseModel):
    titulo: str | None = Field(default=None, max_length=1000)


class ItemMutationOut(BaseModel):
    item_count: int
    saved: bool
