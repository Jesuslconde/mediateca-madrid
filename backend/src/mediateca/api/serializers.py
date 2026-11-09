from __future__ import annotations

from typing import Any

from mediateca.catalog.models import Edicion


def serialize_record(edicion: Edicion) -> dict[str, Any]:
    return {
        "titn": edicion.titn,
        "titulo": edicion.titulo,
        "titulo_uniforme": edicion.titulo_uniforme,
        "publicacion": edicion.publicacion,
        "anio": edicion.anio,
        "idioma": edicion.idioma,
        "pais": edicion.pais,
        "duracion_min": edicion.duracion_min,
        "edad_recomendada": edicion.edad_recomendada,
        "sinopsis": edicion.sinopsis,
        "generos": edicion.generos or [],
        "materias": [relacion.materia.termino for relacion in edicion.materias],
        "soportes": edicion.soportes or [],
        "soporte_principal": edicion.soporte_principal,
        "ean": edicion.ean,
        "tipo_documento": edicion.tipo_documento,
        "disponible": edicion.disponible,
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
                "estado": ejemplar.estado,
                "disponible": ejemplar.disponible,
            }
            for ejemplar in edicion.ejemplares
        ],
        "obra": (
            {
                "id": edicion.obra.id,
                "titulo_uniforme": edicion.obra.titulo_uniforme,
                "anio": edicion.obra.anio,
                "director_principal": edicion.obra.director_principal,
            }
            if edicion.obra
            else None
        ),
        "notas": edicion.notas or {},
        "marc": edicion.marc or {},
        "source_url": edicion.source_url,
        "updated_at": edicion.updated_at.isoformat() if edicion.updated_at else None,
    }
