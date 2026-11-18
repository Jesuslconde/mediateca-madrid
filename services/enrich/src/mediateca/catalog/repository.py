from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from mediateca_shared.identity import compose_record_id, normalize_record_id
from mediateca_shared.models import (
    Biblioteca,
    Edicion,
    EdicionMateria,
    EdicionPersona,
    Ejemplar,
    Enlace,
    Fuente,
    Materia,
    Obra,
    Persona,
    Sucursal,
)
from mediateca_shared.soportes import soporte_principal
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mediateca.catalog.jobs import mark_enriched
from mediateca.catalog.parser import ParsedEdicion

if TYPE_CHECKING:
    from mediateca.catalog.directory import ParsedSucursal


def _fold(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold().strip()


def normalize_name(value: str) -> str:
    text = _fold(value)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str) -> str:
    text = _fold(value)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "desconocida"


def _external_key(parsed: ParsedEdicion, ejemplar) -> str:
    raw = "|".join(
        [
            parsed.titn,
            ejemplar.biblioteca_codigo or "",
            ejemplar.sucursal_codigo or "",
            ejemplar.signatura or "",
            ejemplar.soporte or "",
            ejemplar.tipo_ejemplar or "",
            ejemplar.codigo_barras or "",
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _director_principal(parsed: ParsedEdicion) -> str | None:
    for persona in parsed.personas:
        for role in persona.roles:
            if "director" in role.casefold():
                return persona.nombre
    return None


def get_or_create_obra(session: Session, parsed: ParsedEdicion) -> Obra:
    titulo = parsed.titulo_uniforme or parsed.titulo
    stmt = select(Obra).where(Obra.titulo_uniforme == titulo)
    if parsed.anio is None:
        stmt = stmt.where(Obra.anio.is_(None))
    else:
        stmt = stmt.where(Obra.anio == parsed.anio)

    with session.no_autoflush:
        obra = session.scalars(stmt).first()
        if obra is None:
            obra = Obra(
                titulo_uniforme=titulo,
                anio=parsed.anio,
                director_principal=_director_principal(parsed),
            )
            session.add(obra)
            session.flush()
        elif obra.director_principal is None:
            obra.director_principal = _director_principal(parsed)
    return obra


def get_or_create_biblioteca(
    session: Session, fuente_id: int, codigo: str | None, nombre: str
) -> Biblioteca:
    code = codigo if codigo and codigo != "DESCONOCIDA" else slugify(nombre)
    biblioteca = session.scalars(
        select(Biblioteca).where(
            Biblioteca.fuente_id == fuente_id,
            Biblioteca.codigo == code,
        )
    ).first()
    if biblioteca is None:
        biblioteca = Biblioteca(fuente_id=fuente_id, codigo=code, nombre=nombre)
        session.add(biblioteca)
        session.flush()
    elif nombre and biblioteca.nombre != nombre:
        biblioteca.nombre = nombre
    return biblioteca


def update_biblioteca_location(
    session: Session, biblioteca: Biblioteca, parsed: ParsedSucursal
) -> None:
    """Actualiza la ubicacion de respaldo de una biblioteca sin borrar datos."""
    if parsed.municipio is not None:
        biblioteca.municipio = parsed.municipio
    if parsed.direccion is not None:
        biblioteca.direccion = parsed.direccion
    if parsed.codigo_postal is not None:
        biblioteca.codigo_postal = parsed.codigo_postal
    if parsed.latitud is not None:
        biblioteca.latitud = parsed.latitud
    if parsed.longitud is not None:
        biblioteca.longitud = parsed.longitud
    session.flush()


def upsert_sucursal(
    session: Session, biblioteca: Biblioteca, parsed: ParsedSucursal
) -> Sucursal:
    """Crea o actualiza una sucursal por codigo, sin duplicados ni borrados."""
    if parsed.sucursal_codigo is None:
        raise ValueError("La ficha del directorio no tiene codigo de sucursal")

    sucursal = session.scalars(
        select(Sucursal).where(
            Sucursal.fuente_id == biblioteca.fuente_id,
            Sucursal.codigo == parsed.sucursal_codigo,
        )
    ).first()
    if sucursal is None:
        sucursal = Sucursal(
            fuente_id=biblioteca.fuente_id,
            biblioteca=biblioteca,
            codigo=parsed.sucursal_codigo,
            nombre=parsed.nombre,
            municipio=parsed.municipio,
            direccion=parsed.direccion,
            codigo_postal=parsed.codigo_postal,
            latitud=parsed.latitud,
            longitud=parsed.longitud,
        )
        session.add(sucursal)
    else:
        sucursal.biblioteca = biblioteca
        if parsed.nombre:
            sucursal.nombre = parsed.nombre
        if parsed.municipio is not None:
            sucursal.municipio = parsed.municipio
        if parsed.direccion is not None:
            sucursal.direccion = parsed.direccion
        if parsed.codigo_postal is not None:
            sucursal.codigo_postal = parsed.codigo_postal
        if parsed.latitud is not None:
            sucursal.latitud = parsed.latitud
        if parsed.longitud is not None:
            sucursal.longitud = parsed.longitud
    session.flush()
    return sucursal


def _get_or_create_persona(session: Session, nombre: str) -> Persona:
    normalized = normalize_name(nombre)
    persona = session.scalars(
        select(Persona).where(Persona.nombre_normalizado == normalized)
    ).first()
    if persona is None:
        persona = Persona(nombre=nombre, nombre_normalizado=normalized)
        session.add(persona)
        session.flush()
    return persona


def _get_or_create_materia(session: Session, termino: str) -> Materia:
    clean_termino = termino.strip()
    normalized = clean_termino.casefold()
    materia = session.scalars(
        select(Materia).where(func.lower(Materia.termino) == normalized)
    ).first()
    if materia is None:
        materia = Materia(termino=clean_termino)
        session.add(materia)
        session.flush()
    elif materia.termino != clean_termino:
        materia.termino = clean_termino
    return materia


def _sync_personas(session: Session, edicion: Edicion, parsed: ParsedEdicion) -> None:
    order = 0
    for parsed_persona in parsed.personas:
        persona = _get_or_create_persona(session, parsed_persona.nombre)
        for role in parsed_persona.roles or ["autor"]:
            edicion.personas.append(
                EdicionPersona(persona=persona, rol=role, orden=order)
            )
            order += 1


def _sync_materias(session: Session, edicion: Edicion, parsed: ParsedEdicion) -> None:
    for termino in parsed.materias:
        materia = _get_or_create_materia(session, termino)
        edicion.materias.append(EdicionMateria(materia=materia))


def _sync_enlaces(edicion: Edicion, parsed: ParsedEdicion) -> None:
    for parsed_enlace in parsed.enlaces:
        edicion.enlaces.append(
            Enlace(url=parsed_enlace.url, etiqueta=parsed_enlace.etiqueta)
        )


def _sync_ejemplares(
    session: Session, edicion: Edicion, parsed: ParsedEdicion, fuente_id: int
) -> None:
    existing = {ejemplar.external_key: ejemplar for ejemplar in edicion.ejemplares}
    seen_keys: set[str] = set()

    for parsed_ejemplar in parsed.ejemplares:
        key = _external_key(parsed, parsed_ejemplar)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        biblioteca = get_or_create_biblioteca(
            session,
            fuente_id,
            parsed_ejemplar.biblioteca_codigo,
            parsed_ejemplar.biblioteca_nombre,
        )
        ejemplar = existing.get(key)
        if ejemplar is None:
            ejemplar = Ejemplar(
                fuente_id=fuente_id,
                external_key=key,
                biblioteca=biblioteca,
                sucursal_codigo=parsed_ejemplar.sucursal_codigo,
                sucursal_nombre=parsed_ejemplar.sucursal_nombre,
                localizacion=parsed_ejemplar.localizacion,
                signatura=parsed_ejemplar.signatura,
                tipo_ejemplar=parsed_ejemplar.tipo_ejemplar,
                soporte=parsed_ejemplar.soporte,
            )
            edicion.ejemplares.append(ejemplar)
        else:
            ejemplar.biblioteca = biblioteca
            ejemplar.sucursal_codigo = parsed_ejemplar.sucursal_codigo
            ejemplar.sucursal_nombre = parsed_ejemplar.sucursal_nombre
            ejemplar.localizacion = parsed_ejemplar.localizacion
            ejemplar.signatura = parsed_ejemplar.signatura
            ejemplar.tipo_ejemplar = parsed_ejemplar.tipo_ejemplar
            ejemplar.soporte = parsed_ejemplar.soporte


def upsert_edicion(
    session: Session, parsed: ParsedEdicion, *, fuente: Fuente | None = None
) -> Edicion:
    if fuente is None:
        from mediateca.catalog.fuentes import ensure_default_fuente

        fuente = ensure_default_fuente(session)
    obra = get_or_create_obra(session, parsed)

    record_id = compose_record_id(fuente.codigo, parsed.titn)
    edicion = session.scalars(
        select(Edicion).where(Edicion.record_id == record_id)
    ).first()
    if edicion is None:
        edicion = Edicion(
            fuente_id=fuente.id,
            record_id=record_id,
            titn=parsed.titn,
            titulo=parsed.titulo,
            obra=obra,
        )
        session.add(edicion)

    edicion.fuente_id = fuente.id
    edicion.record_id = record_id
    edicion.obra = obra
    edicion.titulo = parsed.titulo
    edicion.titulo_uniforme = parsed.titulo_uniforme
    edicion.publicacion = parsed.publicacion
    edicion.anio = parsed.anio
    edicion.idioma = parsed.idioma
    edicion.pais = parsed.pais
    edicion.duracion_min = parsed.duracion_min
    edicion.edad_recomendada = parsed.edad_recomendada
    edicion.sinopsis = parsed.sinopsis
    edicion.generos = parsed.generos
    edicion.soportes = parsed.soportes
    edicion.soporte_principal = soporte_principal(parsed.soportes)
    edicion.ean = parsed.ean
    edicion.tipo_documento = parsed.tipo_documento
    edicion.notas = parsed.notas
    edicion.marc = parsed.marc
    edicion.source_url = parsed.source_url

    edicion.personas.clear()
    edicion.materias.clear()
    edicion.enlaces.clear()
    session.flush()

    _sync_personas(session, edicion, parsed)
    _sync_materias(session, edicion, parsed)
    _sync_enlaces(edicion, parsed)
    _sync_ejemplares(session, edicion, parsed, fuente.id)

    timestamp = datetime.now(UTC)
    if edicion.discovery_seen_at is None:
        edicion.discovery_seen_at = timestamp
    mark_enriched(session, edicion, fetched_at=timestamp)
    record_enrich_success(session, edicion, at=timestamp)

    session.flush()
    return edicion


def upsert_stub(
    session: Session, parsed: ParsedEdicion, *, fuente: Fuente | None = None
) -> Edicion:
    if fuente is None:
        from mediateca.catalog.fuentes import ensure_default_fuente

        fuente = ensure_default_fuente(session)
    timestamp = datetime.now(UTC)
    record_id = compose_record_id(fuente.codigo, parsed.titn)
    edicion = session.scalars(
        select(Edicion).where(Edicion.record_id == record_id)
    ).first()

    if edicion is None:
        edicion = Edicion(
            fuente_id=fuente.id,
            record_id=record_id,
            titn=parsed.titn,
            titulo=parsed.titulo,
            publicacion=parsed.publicacion,
            anio=parsed.anio,
            idioma=parsed.idioma,
            pais=parsed.pais,
            duracion_min=parsed.duracion_min,
            generos=parsed.generos,
            soportes=parsed.soportes,
            soporte_principal=soporte_principal(parsed.soportes),
            ean=parsed.ean,
            tipo_documento=parsed.tipo_documento,
            notas=parsed.notas,
            marc=parsed.marc,
            source_url=parsed.source_url,
            is_stub=True,
            discovery_seen_at=timestamp,
        )
        session.add(edicion)
        session.flush()
        return edicion

    edicion.discovery_seen_at = timestamp
    edicion.missing_at = None

    if edicion.is_stub:
        edicion.titulo = parsed.titulo or edicion.titulo
        edicion.publicacion = parsed.publicacion
        edicion.anio = parsed.anio
        edicion.idioma = parsed.idioma
        edicion.pais = parsed.pais
        edicion.duracion_min = parsed.duracion_min
        edicion.generos = parsed.generos
        edicion.soportes = parsed.soportes
        edicion.soporte_principal = soporte_principal(parsed.soportes)
        edicion.ean = parsed.ean
        edicion.tipo_documento = parsed.tipo_documento
        edicion.notas = parsed.notas
        edicion.marc = parsed.marc
        edicion.source_url = parsed.source_url

    session.flush()
    return edicion


def apply_tmdb_enrichment(
    session: Session,
    edicion: Edicion,
    *,
    paises_origen: list[str],
    tmdb_id: int,
    poster_url: str | None = None,
    tmdb_url: str | None = None,
    enriched_at: datetime | None = None,
) -> None:
    """Actualiza los campos TMDB sin tocar el pais del OPAC."""
    edicion.paises_origen = list(paises_origen)
    edicion.tmdb_id = tmdb_id
    edicion.tmdb_poster_url = poster_url
    edicion.tmdb_url = tmdb_url
    edicion.tmdb_enriched_at = enriched_at or datetime.now(UTC)
    session.flush()


def record_enrich_success(
    session: Session,
    edicion: Edicion,
    *,
    at: datetime | None = None,
) -> None:
    edicion.enrich_status = "enriched"
    edicion.enrich_attempts = (edicion.enrich_attempts or 0) + 1
    edicion.enrich_last_attempt_at = at or datetime.now(UTC)
    edicion.enrich_last_error = None
    session.flush()


def record_enrich_failure(
    session: Session,
    record_id: str,
    error: str,
    *,
    at: datetime | None = None,
) -> None:
    normalized = normalize_record_id(record_id)
    edicion = session.scalars(
        select(Edicion).where(Edicion.record_id == normalized)
    ).first()
    if edicion is None:
        return
    edicion.enrich_status = "failed"
    edicion.enrich_attempts = (edicion.enrich_attempts or 0) + 1
    edicion.enrich_last_attempt_at = at or datetime.now(UTC)
    edicion.enrich_last_error = error
    session.flush()


def record_tmdb_outcome(
    session: Session,
    edicion: Edicion,
    status: str,
    *,
    error: str | None = None,
    at: datetime | None = None,
) -> None:
    edicion.tmdb_status = status
    if status == "skipped":
        edicion.tmdb_last_error = None
    else:
        edicion.tmdb_attempts = (edicion.tmdb_attempts or 0) + 1
        edicion.tmdb_last_attempt_at = at or datetime.now(UTC)
        edicion.tmdb_last_error = error
    session.flush()


def mark_absent_since(
    session: Session,
    seen_record_ids: Iterable[str],
    *,
    fuente_id: int | None = None,
    since: datetime,
    missing_at: datetime | None = None,
) -> int:
    """Marca como ausentes las ediciones no vistas desde ``since``."""
    seen = {normalize_record_id(value) for value in seen_record_ids}
    stmt = select(Edicion).where(
        Edicion.discovery_seen_at.is_not(None),
        Edicion.discovery_seen_at < since,
    )
    if fuente_id is not None:
        stmt = stmt.where(Edicion.fuente_id == fuente_id)
    if seen:
        stmt = stmt.where(Edicion.record_id.not_in(seen))

    timestamp = missing_at or datetime.now(UTC)
    ausentes = 0
    for edicion in session.scalars(stmt):
        if edicion.missing_at is None:
            edicion.missing_at = timestamp
            ausentes += 1
    session.flush()
    return ausentes


def select_pending_titns(
    session: Session,
    *,
    fuente_id: int | None = None,
    limit: int = 5000,
    after_titn: str | None = None,
    since: datetime | None = None,
) -> list[str]:
    """Devuelve hasta ``limit`` record_id pendientes de enriquecer."""
    stmt = select(Edicion.record_id).where(Edicion.detail_fetched_at.is_(None))
    if fuente_id is not None:
        stmt = stmt.where(Edicion.fuente_id == fuente_id)
    if after_titn is not None:
        stmt = stmt.where(Edicion.titn > after_titn)
    if since is not None:
        stmt = stmt.where(Edicion.discovery_seen_at >= since)
    stmt = stmt.order_by(Edicion.titn).limit(limit)
    return list(session.scalars(stmt))


def count_pending_titns(
    session: Session,
    *,
    fuente_id: int | None = None,
    since: datetime | None = None,
    after_titn: str | None = None,
) -> int:
    stmt = select(func.count(Edicion.id)).where(Edicion.detail_fetched_at.is_(None))
    if fuente_id is not None:
        stmt = stmt.where(Edicion.fuente_id == fuente_id)
    if after_titn is not None:
        stmt = stmt.where(Edicion.titn > after_titn)
    if since is not None:
        stmt = stmt.where(Edicion.discovery_seen_at >= since)
    return int(session.scalar(stmt) or 0)
