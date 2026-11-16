from __future__ import annotations

import re
import unicodedata

TRAILING_PUNCTUATION = re.compile(r"\s*[/:;,=.]+$")
WHITESPACE = re.compile(r"\s+")
RESPONSIBILITY = re.compile(r"\s+/\s*")
FORM_QUALIFIER = re.compile(
    r"\s*\(\s*"
    r"(?:pel[ií]cula\s+cinematogr[aá]fica|videograbaci[oó]n|"
    r"documental|miniserie|serie|programa|grabaci[oó]n|"
    r"edici[oó]n|versi[oó]n)"
    r"(?:\s*[:;]\s*[^)]*)?"
    r"\s*\)\s*$",
    re.IGNORECASE,
)
INVISIBLE_SEPARATORS = frozenset({"\u00ad", "\u200b", "\u200c", "\ufeff"})


def clean_title(value: str | None) -> str | None:
    """Normaliza un título para mostrarlo y buscarlo.

    Conserva ``?``, ``!``, corchetes y paréntesis; elimina controles,
    separadores invisibles y la puntuación ISBD final.
    """
    if value is None:
        return None

    text = unicodedata.normalize("NFC", str(value))
    text = text.replace("\u00a0", " ")
    text = "".join(
        " " if char in INVISIBLE_SEPARATORS else char
        for char in text
    )
    text = "".join(
        char
        for char in text
        if char in "\n\r\t" or unicodedata.category(char) != "Cf"
    )
    text = "".join(
        char for char in text if char in "\n\r\t" or unicodedata.category(char) != "Cc"
    )
    text = WHITESPACE.sub(" ", text).strip()
    text = TRAILING_PUNCTUATION.sub("", text).strip()
    return text or None


def split_responsibility(value: str | None) -> str | None:
    """Devuelve la parte anterior a la mención de responsabilidad."""
    if not value:
        return None
    head = RESPONSIBILITY.split(value, maxsplit=1)[0].strip()
    return head or None


def strip_form_qualifier(value: str | None) -> str | None:
    """Quita calificadores de forma finales usados en títulos uniformes."""
    text = clean_title(value)
    if not text:
        return None
    while True:
        cleaned = FORM_QUALIFIER.sub("", text).strip()
        if cleaned == text:
            break
        text = cleaned
    return clean_title(text)
