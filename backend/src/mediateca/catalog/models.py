from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mediateca.core.db import Base


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titn: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    obra_id: Mapped[int] = mapped_column(
        ForeignKey("obras.id", ondelete="CASCADE"), index=True
    )

    titulo: Mapped[str] = mapped_column(String(1000))
    titulo_uniforme: Mapped[str | None] = mapped_column(String(1000))
    publicacion: Mapped[str | None] = mapped_column(Text)
    anio: Mapped[int | None] = mapped_column(Integer, index=True)
    idioma: Mapped[str | None] = mapped_column(String(16), index=True)
    pais: Mapped[str | None] = mapped_column(String(16), index=True)
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
    disponible: Mapped[bool | None] = mapped_column(Boolean, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    obra: Mapped[Obra] = relationship(back_populates="ediciones")
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
    snapshots: Mapped[list[Snapshot]] = relationship(back_populates="edicion")


class Biblioteca(Base):
    __tablename__ = "bibliotecas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(500), index=True)
    municipio: Mapped[str | None] = mapped_column(String(250), index=True)
    direccion: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)

    ejemplares: Mapped[list[Ejemplar]] = relationship(back_populates="biblioteca")


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
    estado: Mapped[str | None] = mapped_column(String(120))
    disponible: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    edicion: Mapped[Edicion] = relationship(back_populates="ejemplares")
    biblioteca: Mapped[Biblioteca] = relationship(back_populates="ejemplares")
    historial: Mapped[list[HistorialDisponibilidad]] = relationship(
        back_populates="ejemplar", cascade="all, delete-orphan"
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


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicion_id: Mapped[int | None] = mapped_column(
        ForeignKey("ediciones.id", ondelete="SET NULL"), index=True
    )
    titn: Mapped[str] = mapped_column(String(32), index=True)
    url: Mapped[str] = mapped_column(Text)
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    edicion: Mapped[Edicion | None] = relationship(back_populates="snapshots")


class HistorialDisponibilidad(Base):
    __tablename__ = "historial_disponibilidad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ejemplar_id: Mapped[int] = mapped_column(
        ForeignKey("ejemplares.id", ondelete="CASCADE"), index=True
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    disponible: Mapped[bool] = mapped_column(Boolean)
    estado: Mapped[str | None] = mapped_column(String(120))

    ejemplar: Mapped[Ejemplar] = relationship(back_populates="historial")


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
