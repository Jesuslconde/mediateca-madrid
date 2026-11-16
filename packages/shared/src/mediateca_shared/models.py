from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mediateca_shared.db import Base


class Obra(Base):
    __tablename__ = "obras"
    __table_args__ = (UniqueConstraint("titulo_uniforme", "anio", name="uq_obra_titulo_anio"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo_uniforme: Mapped[str] = mapped_column(String(1000), index=True)
    anio: Mapped[int | None] = mapped_column(Integer, index=True)
    director_principal: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ediciones: Mapped[list[Edicion]] = relationship(back_populates="obra")


class Edicion(Base):
    __tablename__ = "ediciones"
    __table_args__ = (
        Index("ix_ediciones_enrich_status_titn", "enrich_status", "titn"),
        Index("ix_ediciones_tmdb_status_titn", "tmdb_status", "titn"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titn: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    obra_id: Mapped[int | None] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE"), index=True
    )

    titulo: Mapped[str] = mapped_column(String(1000))
    titulo_uniforme: Mapped[str | None] = mapped_column(String(1000))
    publicacion: Mapped[str | None] = mapped_column(Text)
    anio: Mapped[int | None] = mapped_column(Integer, index=True)
    idioma: Mapped[str | None] = mapped_column(String(16), index=True)
    pais: Mapped[str | None] = mapped_column(String(16), index=True)
    paises_origen: Mapped[list[str]] = mapped_column(JSON, default=list)
    tmdb_id: Mapped[int | None] = mapped_column(Integer)
    tmdb_poster_url: Mapped[str | None] = mapped_column(Text)
    tmdb_url: Mapped[str | None] = mapped_column(Text)
    tmdb_enriched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    enrich_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    enrich_attempts: Mapped[int] = mapped_column(Integer, default=0)
    enrich_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrich_last_error: Mapped[str | None] = mapped_column(Text)
    tmdb_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    tmdb_attempts: Mapped[int] = mapped_column(Integer, default=0)
    tmdb_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tmdb_last_error: Mapped[str | None] = mapped_column(Text)
    duracion_min: Mapped[int | None] = mapped_column(Integer)
    edad_recomendada: Mapped[str | None] = mapped_column(String(250))
    sinopsis: Mapped[str | None] = mapped_column(Text)
    generos: Mapped[list[str]] = mapped_column(JSON, default=list)
    soportes: Mapped[list[str]] = mapped_column(JSON, default=list)
    soporte_principal: Mapped[str | None] = mapped_column(String(32), index=True)
    ean: Mapped[str | None] = mapped_column(String(64), index=True)
    tipo_documento: Mapped[str | None] = mapped_column(String(120))
    notas: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    marc: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_url: Mapped[str | None] = mapped_column(Text)
    is_stub: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    discovery_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    detail_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    missing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    obra: Mapped[Obra | None] = relationship(back_populates="ediciones")
    ejemplares: Mapped[list[Ejemplar]] = relationship(
        back_populates="edicion", cascade="all, delete-orphan"
    )
    personas: Mapped[list[EdicionPersona]] = relationship(
        back_populates="edicion", cascade="all, delete-orphan"
    )
    materias: Mapped[list[EdicionMateria]] = relationship(
        back_populates="edicion", cascade="all, delete-orphan"
    )
    enlaces: Mapped[list[Enlace]] = relationship(
        back_populates="edicion", cascade="all, delete-orphan"
    )


class Biblioteca(Base):
    __tablename__ = "bibliotecas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(500), index=True)
    municipio: Mapped[str | None] = mapped_column(String(250), index=True)
    direccion: Mapped[str | None] = mapped_column(Text)
    codigo_postal: Mapped[str | None] = mapped_column(String(5))
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)

    ejemplares: Mapped[list[Ejemplar]] = relationship(back_populates="biblioteca")
    sucursales: Mapped[list[Sucursal]] = relationship(
        back_populates="biblioteca", cascade="all, delete-orphan"
    )


class Sucursal(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    biblioteca_id: Mapped[int] = mapped_column(
        ForeignKey("bibliotecas.id", ondelete="CASCADE"), index=True
    )
    codigo: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(500))
    municipio: Mapped[str | None] = mapped_column(String(250), index=True)
    direccion: Mapped[str | None] = mapped_column(Text)
    codigo_postal: Mapped[str | None] = mapped_column(String(5), index=True)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    biblioteca: Mapped[Biblioteca] = relationship(back_populates="sucursales")


class Ejemplar(Base):
    __tablename__ = "ejemplares"
    __table_args__ = (UniqueConstraint("external_key", name="uq_ejemplar_external_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicion_id: Mapped[int] = mapped_column(
        ForeignKey("ediciones.id", ondelete="CASCADE"), index=True
    )
    biblioteca_id: Mapped[int] = mapped_column(
        ForeignKey("bibliotecas.id", ondelete="CASCADE"), index=True
    )
    external_key: Mapped[str] = mapped_column(String(64), index=True)

    sucursal_codigo: Mapped[str | None] = mapped_column(String(64), index=True)
    sucursal_nombre: Mapped[str | None] = mapped_column(String(500))
    localizacion: Mapped[str | None] = mapped_column(String(250))
    signatura: Mapped[str | None] = mapped_column(String(250), index=True)
    tipo_ejemplar: Mapped[str | None] = mapped_column(String(250))
    soporte: Mapped[str | None] = mapped_column(String(64), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    edicion: Mapped[Edicion] = relationship(back_populates="ejemplares")
    biblioteca: Mapped[Biblioteca] = relationship(back_populates="ejemplares")
    sucursal: Mapped[Sucursal | None] = relationship(
        "Sucursal",
        primaryjoin="foreign(Ejemplar.sucursal_codigo) == Sucursal.codigo",
        viewonly=True,
        uselist=False,
    )


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(500))
    nombre_normalizado: Mapped[str] = mapped_column(String(500), unique=True, index=True)

    ediciones: Mapped[list[EdicionPersona]] = relationship(back_populates="persona")


class EdicionPersona(Base):
    __tablename__ = "edicion_persona"
    __table_args__ = (
        UniqueConstraint("edicion_id", "persona_id", "rol", name="uq_edicion_persona_rol"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicion_id: Mapped[int] = mapped_column(
        ForeignKey("ediciones.id", ondelete="CASCADE"), index=True
    )
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.id", ondelete="CASCADE"), index=True
    )
    rol: Mapped[str] = mapped_column(String(120), index=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    edicion: Mapped[Edicion] = relationship(back_populates="personas")
    persona: Mapped[Persona] = relationship(back_populates="ediciones")


class Materia(Base):
    __tablename__ = "materias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    termino: Mapped[str] = mapped_column(String(500), unique=True, index=True)

    ediciones: Mapped[list[EdicionMateria]] = relationship(back_populates="materia")


class EdicionMateria(Base):
    __tablename__ = "edicion_materia"
    __table_args__ = (
        UniqueConstraint("edicion_id", "materia_id", name="uq_edicion_materia"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicion_id: Mapped[int] = mapped_column(
        ForeignKey("ediciones.id", ondelete="CASCADE"), index=True
    )
    materia_id: Mapped[int] = mapped_column(
        ForeignKey("materias.id", ondelete="CASCADE"), index=True
    )

    edicion: Mapped[Edicion] = relationship(back_populates="materias")
    materia: Mapped[Materia] = relationship(back_populates="ediciones")


class Enlace(Base):
    __tablename__ = "enlaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicion_id: Mapped[int] = mapped_column(
        ForeignKey("ediciones.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(Text)
    etiqueta: Mapped[str | None] = mapped_column(String(250))

    edicion: Mapped[Edicion] = relationship(back_populates="enlaces")


class HarvestJob(Base):
    __tablename__ = "harvest_jobs"
    __table_args__ = (Index("ix_harvest_jobs_status_job_type", "status", "job_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    cursor_doc: Mapped[int | None] = mapped_column(Integer)
    cursor_titn: Mapped[str | None] = mapped_column(String(32))
    batch_size: Mapped[int] = mapped_column(Integer, default=5000)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HarvestRun(Base):
    __tablename__ = "harvest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    query: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class SchemaMeta(Base):
    __tablename__ = "schema_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(64))
