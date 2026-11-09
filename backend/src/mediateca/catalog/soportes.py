from __future__ import annotations

import re
import unicodedata

SUPPORT_ORDER = ["4K UHD", "Blu-ray", "DVD", "VHS"]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def _add(found: list[str], value: str) -> None:
    if value not in found:
        found.append(value)


def detect_soportes(
    descripcion_fisica: str | None = None,
    soportes_ejemplar: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    """Detecta soportes normalizados en una descripcion y en los ejemplares.

    Es deliberadamente tolerante: si un registro mezcla DVD y Blu-ray,
    devuelve ambos valores.
    """
    texts = [descripcion_fisica or ""]
    texts.extend(soportes_ejemplar or [])

    found: list[str] = []
    for raw in texts:
        text = normalize_text(raw)
        if not text:
            continue

        if re.search(r"\b(4k|uhd)\b", text) or "ultra hd" in text:
            _add(found, "4K UHD")

        if (
            "blu-ray" in text
            or "blu ray" in text
            or "bluray" in text
            or "blu-ray disc" in text
            or re.search(r"\bbd\b", text)
        ):
            _add(found, "Blu-ray")

        if "dvd" in text and "dvd-rom" not in text and "dvd rom" not in text:
            _add(found, "DVD")

        if re.search(r"\bvhs\b", text):
            _add(found, "VHS")

    return [item for item in SUPPORT_ORDER if item in found]


def canonical_soporte(value: str | None) -> str | None:
    """Normaliza un unico valor de soporte proveniente de un ejemplar."""
    detected = detect_soportes(value)
    if detected:
        return detected[0]
    if value:
        return re.sub(r"\s+", " ", value).strip()
    return None


def soporte_principal(soportes: list[str]) -> str | None:
    if not soportes:
        return None
    if len(soportes) == 1:
        return soportes[0]
    return "Varios"
