from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from mediateca_shared.models import Fuente

VIDEO_RE = re.compile(r"videograb|v[ií]deos?|bideo|dvd|pel[ií]culas?", re.I)
SESSION_COMPONENT_RE = re.compile(r"^[A-Za-z0-9]{8,}$")
DEFAULT_USER_AGENT = (
    "MediatecaMadrid/0.1 (portal alternativo de consulta; "
    "contacto: mediateca@example.org)"
)


class CalibrationError(RuntimeError):
    """No se pudo calibrar el perfil de una fuente."""


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    session_pattern: str
    format_value: str
    format_label: str
    session_url: str


def _resolve_session_url(response: httpx.Response) -> str:
    match = re.search(r"URL=([^\"'>\s]+)", response.text)
    if match:
        return urljoin(str(response.url), match.group(1))
    return str(response.url)


def extract_session_pattern(url: str) -> tuple[str, str]:
    """Devuelve ``(sid, patron)`` a partir de una URL de sesion del OPAC."""
    parts = [part for part in urlparse(url).path.split("/") if part]
    if len(parts) < 2 or not SESSION_COMPONENT_RE.match(parts[-1]):
        raise CalibrationError(f"No se pudo detectar la sesion del OPAC en {url}")
    segment = parts[-2]
    return parts[-1], f"/{segment}/([A-Za-z0-9]+)"


def extract_video_option(html: str) -> tuple[str, str] | None:
    """Busca la opcion de videograbaciones en el selector ``select03``."""
    soup = BeautifulSoup(html, "lxml")
    for select in soup.find_all("select"):
        if select.get("name") != "select03":
            continue
        for option in select.find_all("option"):
            label = option.get_text(" ", strip=True)
            lowered = label.lower()
            if not VIDEO_RE.search(label):
                continue
            if "juego" in lowered or "cd-rom" in lowered:
                continue
            value = option.get("value")
            if value:
                return str(value), label
    return None


def calibrate_source(
    fuente: Fuente, *, client: httpx.Client | None = None
) -> CalibrationResult:
    """Detecta el patron de sesion y el codigo de video de una fuente."""
    options = fuente.options or {}
    owns_client = client is None
    if client is None:
        client = httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            verify=options.get("verify_tls", True) is not False,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "es-ES,es;q=0.9"},
        )
    try:
        opac_url = fuente.base_url.rstrip("/") + (fuente.opac_path or "")
        response = client.get(opac_url, params={"ACC": 101})
        response.raise_for_status()
        session_url = _resolve_session_url(response)
        if session_url != str(response.url):
            response = client.get(session_url)
            response.raise_for_status()

        _sid, pattern = extract_session_pattern(session_url)
        base_session = session_url.split("?", 1)[0]
        candidates = (session_url, f"{base_session}?ACC=120&FORM=2")
        for candidate in candidates:
            try:
                page = client.get(candidate)
                page.raise_for_status()
            except httpx.HTTPError:
                continue
            found = extract_video_option(page.text)
            if found is not None:
                value, label = found
                return CalibrationResult(
                    session_pattern=pattern,
                    format_value=value,
                    format_label=label,
                    session_url=session_url,
                )
        raise CalibrationError(
            f"La fuente {fuente.codigo} no declara un codigo de video en select03"
        )
    finally:
        if owns_client:
            client.close()
