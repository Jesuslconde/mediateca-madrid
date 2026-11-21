from __future__ import annotations

from typing import Any

from mediateca_shared.fuentes import MADRID_PROFILE, FuenteProfile
from mediateca_shared.models import Edicion, Ejemplar


def _profile(edicion: Edicion) -> FuenteProfile:
    if edicion.fuente is None:
        return MADRID_PROFILE
    return FuenteProfile.from_model(edicion.fuente)


def _ubicacion(ejemplar: Ejemplar) -> dict[str, Any] | None:
    """Resuelve la ubicacion del ejemplar: sucursal, biblioteca o nada."""
    if ejemplar.sucursal is not None:
        datos = {
            "codigo_postal": ejemplar.sucursal.codigo_postal,
            "municipio": ejemplar.sucursal.municipio,
            "latitud": ejemplar.sucursal.latitud,
            "longitud": ejemplar.sucursal.longitud,
        }
    else:
        datos = {
            "codigo_postal": ejemplar.biblioteca.codigo_postal,
            "municipio": ejemplar.biblioteca.municipio,
            "latitud": ejemplar.biblioteca.latitud,
            "longitud": ejemplar.biblioteca.longitud,
        }
    if all(value is None for value in datos.values()):
        return None
    return datos


def _serialize_obra_edicion(edicion: Edicion) -> dict[str, Any]:
    profile = _profile(edicion)
    return {
        "record_id": edicion.record_id,
        "fuente": profile.codigo,
        "fuente_nombre": profile.nombre,
        "titn": edicion.titn,
        "titulo": edicion.titulo,
        "anio": edicion.anio,
        "soportes": edicion.soportes or [],
        "ean": edicion.ean,
        "ejemplares": len(edicion.ejemplares),
        "source_url": profile.source_url(edicion.titn),
    }


def serialize_record(
    edicion: Edicion, *, ediciones_obra: list[Edicion] | None = None
) -> dict[str, Any]:
    profile = _profile(edicion)
    hermanas = ediciones_obra if ediciones_obra is not None else [edicion]
    return {
        "record_id": edicion.record_id,
        "fuente": profile.codigo,
        "fuente_nombre": profile.nombre,
        "titn": edicion.titn,
        "titulo": edicion.titulo,
        "titulo_uniforme": edicion.titulo_uniforme,
        "publicacion": edicion.publicacion,
        "anio": edicion.anio,
        "idioma": edicion.idioma,
        "pais": edicion.pais,
        "paises_origen": edicion.paises_origen or [],
        "tmdb_poster_url": edicion.tmdb_poster_url,
        "tmdb_url": edicion.tmdb_url,
        "duracion_min": edicion.duracion_min,
        "edad_recomendada": edicion.edad_recomendada,
        "sinopsis": edicion.sinopsis,
        "generos": edicion.generos or [],
        "materias": [relacion.materia.termino for relacion in edicion.materias],
        "soportes": edicion.soportes or [],
        "soporte_principal": edicion.soporte_principal,
        "ean": edicion.ean,
        "tipo_documento": edicion.tipo_documento,
        "personas": [
            {"nombre": relacion.persona.nombre, "rol": relacion.rol}
            for relacion in edicion.personas
        ],
        "enlaces": [
            {"url": enlace.url, "etiqueta": enlace.etiqueta}
            for enlace in edicion.enlaces
        ],
        "ejemplares": [
            {
                "id": ejemplar.id,
                "biblioteca": ejemplar.biblioteca.nombre,
                "biblioteca_codigo": ejemplar.biblioteca.codigo,
                "sucursal": ejemplar.sucursal_nombre,
                "sucursal_codigo": ejemplar.sucursal_codigo,
                "localizacion": ejemplar.localizacion,
                "signatura": ejemplar.signatura,
                "tipo_ejemplar": ejemplar.tipo_ejemplar,
                "soporte": ejemplar.soporte,
                "ubicacion": _ubicacion(ejemplar),
            }
            for ejemplar in edicion.ejemplares
        ],
        "obra": (
            {
                "id": edicion.obra.id,
                "titulo_uniforme": edicion.obra.titulo_uniforme,
                "anio": edicion.obra.anio,
                "director_principal": edicion.obra.director_principal,
                "ediciones": [
                    _serialize_obra_edicion(hermana) for hermana in hermanas
                ],
            }
            if edicion.obra
            else None
        ),
        "notas": edicion.notas or {},
        "marc": edicion.marc or {},
        "source_url": profile.source_url(edicion.titn),
        "updated_at": edicion.updated_at.isoformat() if edicion.updated_at else None,
    }
