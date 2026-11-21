from __future__ import annotations

import re
import unicodedata

SUPPORT_ORDER = ["4K UHD", "Blu-ray", "DVD", "VHS"]

AUDIOVISUAL_HINT_RE = re.compile(
    r"video-?casete|video-?cinta|videodisco|videograbaci|videorecording|"
    r"\bvideo\b|dvd|blu-?ray|vhs|4k|uhd|betacam|betamax|laserdisc|hd-?dvd|umd|"
    r"disco versatil digital"
)

CD_AUDIO_ROM_RE = re.compile(
    r"\bcd\b|cd[-\s]?(?:da|ad|rom)|\bdvd[-\s]?rom\b|disco\s+sonoro|"
    r"disco\s+compacto|\bcedes?\b"
)
OPTICAL_VIDEO_RE = re.compile(
    r"videodisco|disco\s+optico|cd[-\s]?video|video[-\s]?cd"
)
VIDEO_CASSETTE_RE = re.compile(r"videocas\w+|vhs|betamax|\bbeta\b")
BARE_VIDEO_RE = re.compile(r"\b\d*\s*video\b")
BARE_DISC_RE = re.compile(r"\b\d*\s*discos?\b")
DURATION_RE = re.compile(r"\b\d{1,3}\s*min")
BARE_CASETE_RE = re.compile(r"\b\d*\s*casetes?\b")
BARE_DISC_ONLY_RE = re.compile(r"^\d*\s*discos?\s*[:;,.+]?$")


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
    tipo_documento: str | None = None,
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

        if re.search(r"dvd[-\s]?video", text):
            _add(found, "DVD")

        if "dvd" in text and "dvd-rom" not in text and "dvd rom" not in text:
            _add(found, "DVD")

        if re.search(r"\bvhs\b", text):
            _add(found, "VHS")

        if OPTICAL_VIDEO_RE.search(text):
            _add(found, "DVD")

        if VIDEO_CASSETTE_RE.search(text):
            _add(found, "VHS")

        if (
            not found
            and tipo_documento
            and "videograbacion" in normalize_text(tipo_documento)
            and BARE_CASETE_RE.search(text)
        ):
            _add(found, "VHS")

        if (
            not found
            and tipo_documento
            and "videograbacion" in normalize_text(tipo_documento)
            and BARE_DISC_ONLY_RE.match(text.strip())
        ):
            _add(found, "DVD")

        if (
            not found
            and BARE_VIDEO_RE.search(text)
            and not BARE_DISC_RE.search(text)
            and not CD_AUDIO_ROM_RE.search(text)
        ):
            _add(found, "VHS")

        if (
            not found
            and DURATION_RE.search(text)
            and not CD_AUDIO_ROM_RE.search(text)
        ):
            _add(found, "DVD")

    if "Blu-ray" in found and "DVD" in found and "dvd" not in normalize_text(
        descripcion_fisica
    ):
        found.remove("DVD")

    if "VHS" in found and any(item in found for item in ("DVD", "Blu-ray")):
        descripcion = normalize_text(descripcion_fisica)
        if "vhs" not in descripcion and "beta" not in descripcion:
            found.remove("VHS")

    return [item for item in SUPPORT_ORDER if item in found]


def detect_audiovisual(
    descripcion_fisica: str | None = None,
    soportes_ejemplar: list[str] | tuple[str, ...] | None = None,
    tipo_documento: str | None = None,
) -> bool | None:
    """Indica si un registro es material audiovisual.

    Devuelve ``True`` si se detecta un soporte audiovisual, ``False`` si la
    descripcion o el soporte existen pero no son audiovisuales y ``None`` si no
    hay informacion suficiente para decidir.
    """
    descripcion = normalize_text(descripcion_fisica)
    if (
        descripcion
        and re.search(r"\b(diapositivas?|transparencias?)\b", descripcion)
        and not AUDIOVISUAL_HINT_RE.search(descripcion)
    ):
        return False

    if detect_soportes(descripcion_fisica, soportes_ejemplar, tipo_documento):
        return True

    texts = [descripcion_fisica or ""]
    texts.extend(soportes_ejemplar or [])
    texts = [text for text in texts if text and text.strip()]
    if not texts:
        return None

    hay_pista = False
    for raw in texts:
        text = re.sub(r"dvd[-\s]?rom", " ", normalize_text(raw))
        if AUDIOVISUAL_HINT_RE.search(text):
            hay_pista = True
            break
    return True if hay_pista else False


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
