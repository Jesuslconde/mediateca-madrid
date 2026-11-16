#!/usr/bin/env python3
"""Genera el JSON de codigos postales de la provincia de Madrid.

Fuentes:
- Centroides: kodens-dev/Spain-Postal-Codes (MIT).
- Municipios: regi-es/ds-codigos-postales-ine-es / INE (CC BY 4.0).
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path

CENTROIDS_URL = (
    "https://raw.githubusercontent.com/kodens-dev/Spain-Postal-Codes/"
    "main/postcodes-centroid.csv"
)
MUNICIPALITIES_URL = (
    "https://raw.githubusercontent.com/regi-es/ds-codigos-postales-ine-es/"
    "master/data/codigos_postales_municipios.csv"
)
OUTPUT = Path(__file__).resolve().parents[1] / "apps" / "web" / "lib" / "codigos-postales-madrid.json"
FUENTE = (
    "Centroides: kodens-dev/Spain-Postal-Codes (MIT); "
    "municipios: INE via regi-es/ds-codigos-postales-ine-es (CC BY 4.0)"
)
LICENCIA = "MIT / CC BY 4.0"


def _download(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
        return response.read().decode("utf-8")


def _load_municipalities() -> dict[str, str]:
    rows = csv.DictReader(io.StringIO(_download(MUNICIPALITIES_URL)))
    result: dict[str, str] = {}
    for row in rows:
        codigo = (row.get("codigo_postal") or "").strip()
        municipio = (row.get("municipio_nombre") or "").strip()
        if not codigo.startswith("28") or not municipio:
            continue
        result.setdefault(codigo.zfill(5), municipio)
    return result


def build() -> dict:
    municipalities = _load_municipalities()
    rows = csv.DictReader(io.StringIO(_download(CENTROIDS_URL)))
    codigos: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        codigo = (row.get("postal_code") or "").strip()
        if not codigo.startswith("28") or codigo in seen:
            continue
        latitud = row.get("centroid_lat")
        longitud = row.get("centroid_lng")
        if not codigo or latitud is None or longitud is None:
            continue
        seen.add(codigo)
        codigos.append(
            {
                "codigo": codigo.zfill(5),
                "municipio": municipalities.get(codigo.zfill(5)),
                "latitud": float(latitud),
                "longitud": float(longitud),
            }
        )

    codigos.sort(key=lambda item: str(item["codigo"]))
    return {"fuente": FUENTE, "licencia": LICENCIA, "codigos": codigos}


def main() -> None:
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Escritos {len(data['codigos'])} codigos postales en {OUTPUT}")


if __name__ == "__main__":
    main()
