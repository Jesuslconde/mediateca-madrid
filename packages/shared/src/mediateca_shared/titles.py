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

MATERIAL_GROUP = re.compile(r"\s*([\[(])([^\[\]()]{1,80})([\])])")
MATERIAL_SEPARATOR = re.compile(r"[^a-z0-9]+")
SQUARE_BRACKET_GROUP = re.compile(r"\s*\[[^\]]*\]")
PAREN_GROUP = re.compile(r"\s*\([^)]*\)")
EMPTY_GROUP = re.compile(r"\s*[\[(]\s*[\])]")

MATERIAL_CORE = frozenset(
    {
        "dvd",
        "dcd",
        "video",
        "videos",
        "vhs",
        "blu",
        "videograbacion",
        "videograbaciones",
        "videograbacin",
        "videocasete",
        "videocasetes",
        "videodisco",
        "videojuego",
        "videojuegos",
        "grabacion",
        "archivo",
        "recurso",
        "material",
        "disco",
        "pelicula",
        "multimedia",
        "enregistrament",
        "4k",
        "uhd",
        "cd",
        "cinta",
        "diapositivas",
        "transparencias",
        "betamax",
        "umd",
        "laserdisc",
        "hd",
    }
)
MATERIAL_ALLOWED = MATERIAL_CORE | frozenset(
    {
        "ray",
        "disc",
        "dis",
        "book",
        "rom",
        "sonora",
        "ordenador",
        "electronico",
        "grafico",
        "proyectable",
        "cartografico",
        "versatil",
        "digital",
        "compacto",
        "p",
        "s",
        "nideo",
        "viedo",
        "vido",
        "vide",
        "vdeo",
        "audiovisual",
        "de",
        "del",
        "la",
        "el",
        "los",
        "las",
        "y",
        "o",
        "con",
    }
)


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


def has_balanced_brackets(value: str | None) -> bool:
    """Indica si los corchetes del texto están equilibrados."""
    text = value or ""
    return text.count("[") == text.count("]")


def _normalize_material_tokens(value: str) -> list[str]:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[()]", " ", text)
    text = MATERIAL_SEPARATOR.sub(" ", text)
    return text.split()


def is_material_qualifier(value: str) -> bool:
    """Indica si un grupo entre corchetes es un calificador de material."""
    tokens = _normalize_material_tokens(value)
    return (
        bool(tokens)
        and any(token in MATERIAL_CORE for token in tokens)
        and all(token in MATERIAL_ALLOWED for token in tokens)
    )


def strip_material_qualifier(value: str | None) -> str | None:
    """Quita calificadores de material como ``[DVD-Vídeo]`` o ``(DVD)``.

    Solo elimina grupos reconocidos como GMD. Conserva corchetes que forman
    parte del título, como ``[Rec]`` o ``[A caixa]``, y corrige corchetes
    desbalanceados que deja el OPAC.
    """
    text = clean_title(value)
    if not text:
        return None

    removed = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal removed
        opener, content, closer = match.group(1), match.group(2), match.group(3)
        if (opener == "[" and closer != "]") or (opener == "(" and closer != ")"):
            return match.group(0)
        if is_material_qualifier(content):
            removed = True
            return " "
        return match.group(0)

    while True:
        previous = text
        text = MATERIAL_GROUP.sub(_replace, text)
        if text == previous:
            break

    empty_text = EMPTY_GROUP.sub(" ", text)
    if empty_text != text:
        removed = True
        text = empty_text

    if not has_balanced_brackets(text):
        text = text.replace("[", " ").replace("]", " ")
        removed = True

    if not removed:
        return clean_title(text)

    text = WHITESPACE.sub(" ", text).strip()
    text = re.sub(r"\s*[;,]\s*\.\s*", ". ", text)
    text = re.sub(r"\s+([.,])", r"\1", text)
    text = re.sub(r"(?<!\.)\.\.(?!\.)", ".", text)
    text = re.sub(r"\s*([:;=])\s*", r" \1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+videograbaciones?\s*$", "", text, flags=re.IGNORECASE)
    text = WHITESPACE.sub(" ", text).strip()

    result = clean_title(text)
    return result or text


def strip_all_brackets(value: str | None) -> str | None:
    """Quita todos los grupos entre corchetes y paréntesis.

    Se usa como candidato adicional para TMDB, nunca para persistir.
    """
    text = clean_title(value)
    if not text:
        return None
    text = SQUARE_BRACKET_GROUP.sub(" ", text)
    text = PAREN_GROUP.sub(" ", text)
    text = WHITESPACE.sub(" ", text).strip()
    return clean_title(text)
