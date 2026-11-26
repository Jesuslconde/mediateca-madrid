from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class PostalCode:
    codigo: str
    municipio: str | None
    latitud: float
    longitud: float


def haversine_km(
    lat_a: float, lon_a: float, lat_b: float, lon_b: float
) -> float:
    """Distancia en linea recta aproximada entre dos puntos, en kilometros."""
    d_lat = math.radians(lat_b - lat_a)
    d_lon = math.radians(lon_b - lon_a)
    lat1 = math.radians(lat_a)
    lat2 = math.radians(lat_b)
    h = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def _data_path() -> Path:
    return Path(__file__).resolve().parent / "codigos_postales.json"


@lru_cache(maxsize=1)
def load_codigos_postales() -> dict[str, PostalCode]:
    """Carga los centroides de codigos postales indexados por codigo."""
    with _data_path().open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return {
        item["codigo"]: PostalCode(
            codigo=item["codigo"],
            municipio=item.get("municipio"),
            latitud=float(item["latitud"]),
            longitud=float(item["longitud"]),
        )
        for item in payload["codigos"]
    }


def centroide(codigo_postal: str | None) -> PostalCode | None:
    """Resuelve un codigo postal a su centroide, o None si es desconocido."""
    if not codigo_postal:
        return None
    codigo = codigo_postal.strip().zfill(5)
    return load_codigos_postales().get(codigo)
