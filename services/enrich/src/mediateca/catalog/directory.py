from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup
from mediateca_shared.fuentes import FuenteProfile
from mediateca_shared.models import Biblioteca, Fuente
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from mediateca.catalog.parser import BS_PARSER, clean
from mediateca.catalog.repository import update_biblioteca_location, upsert_sucursal
from mediateca.core.config import settings
from mediateca.core.logging import get_logger

logger = get_logger(__name__)

DIRECTORY_PATH = "/directorio_publicacion/i18n/comunidades"
RECORD_LINK_RE = re.compile(r"registro\.cmd\?id=(\d+)")
POSITION_RE = re.compile(r"posicion=(\d+)")
SUBC_RE = re.compile(r"SUBC=([^&\"'\s]+)")
LL_RE = re.compile(r"[?&]ll=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
CP_LINE_RE = re.compile(r"^(\d{5})\s+(.+?)(?:\s*\(([^)]+)\))?\s*$")
TIPO_RE = re.compile(r"Tipo biblioteca:\s*([^\n]+)")


class _TransientDirectoryError(httpx.HTTPError):
    pass


class DirectoryUnavailable(RuntimeError):
    pass


def directory_path(fuente: Fuente) -> str | None:
    profile = FuenteProfile.from_model(fuente)
    return (profile.options or {}).get("directory_path")


@dataclass(slots=True)
class ParsedSucursal:
    biblioteca_codigo: str
    sucursal_codigo: str | None
    nombre: str
    municipio: str | None = None
    direccion: str | None = None
    codigo_postal: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    tipo_biblioteca: str | None = None
    movil: bool = False


@dataclass(slots=True)
class RefreshStats:
    records: int = 0
    with_subc: int = 0
    with_postal_code: int = 0
    with_coordinates: int = 0
    branches_matched: int = 0
    libraries_updated: int = 0
    omitted: int = 0
    mobile: int = 0


def parse_directory_list(html: str) -> list[str]:
    """Extrae los identificadores de ficha de una pagina de listado."""
    soup = BeautifulSoup(html, BS_PARSER)
    result: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        match = RECORD_LINK_RE.search(str(anchor["href"]))
        if not match:
            continue
        record_id = match.group(1)
        if record_id not in seen:
            seen.add(record_id)
            result.append(record_id)
    return result


def parse_directory_positions(html: str) -> list[int]:
    """Extrae las posiciones de paginacion de una pagina de listado."""
    soup = BeautifulSoup(html, BS_PARSER)
    positions: set[int] = set()
    for anchor in soup.find_all("a", href=True):
        match = POSITION_RE.search(str(anchor["href"]))
        if match:
            positions.add(int(match.group(1)))
    return sorted(positions)


def _address_parts(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    scope = soup.select_one("div.direccion span.valor") or soup.select_one("div.direccion")
    if scope is None:
        return None, None, None

    lines = [line.strip() for line in scope.get_text("\n", strip=True).splitlines() if line.strip()]
    for index, line in enumerate(lines):
        match = CP_LINE_RE.match(line)
        if not match:
            continue
        codigo_postal = match.group(1)
        municipio = clean(match.group(2))
        direccion = clean(", ".join(lines[:index])) or None
        if direccion and direccion.lower().startswith("dirección:"):
            direccion = clean(direccion.split(":", 1)[1]) or None
        return direccion, municipio, codigo_postal
    return None, None, None


def _subc(soup: BeautifulSoup) -> str | None:
    for anchor in soup.find_all("a", href=True):
        match = SUBC_RE.search(str(anchor["href"]))
        if match:
            return unquote(match.group(1)).strip() or None
    return None


def _tipo_biblioteca(soup: BeautifulSoup) -> str | None:
    match = TIPO_RE.search(soup.get_text("\n", strip=True))
    return clean(match.group(1)) if match else None


def _coordinates(soup: BeautifulSoup) -> tuple[float | None, float | None]:
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        if not any(
            token in href
            for token in ("maps.google", "google.com/maps", "maps.app.goo.gl")
        ):
            continue
        matches = LL_RE.findall(href)
        if not matches:
            continue
        latitud, longitud = matches[-1]
        return float(latitud), float(longitud)
    return None, None


def parse_directory_record(html: str) -> ParsedSucursal | None:
    """Parsea una ficha del directorio; devuelve None si no es utilizable."""
    soup = BeautifulSoup(html, BS_PARSER)
    title = soup.select_one("div.ficha h2") or soup.find("h2")
    nombre = clean(title.get_text(" ", strip=True)) if title is not None else None
    if not nombre or "CERRADA" in nombre.upper():
        return None

    subc = _subc(soup)
    if not subc:
        return None
    parts = [part.strip().upper() for part in subc.split("/") if part.strip()]
    if not parts:
        return None
    biblioteca_codigo = parts[0]
    sucursal_codigo = parts[1] if len(parts) > 1 else None

    direccion, municipio, codigo_postal = _address_parts(soup)
    tipo_biblioteca = _tipo_biblioteca(soup)
    tipo_fold = (tipo_biblioteca or "").casefold()
    movil = "móvil" in tipo_fold or "movil" in tipo_fold or "bibliobus" in tipo_fold

    latitud, longitud = _coordinates(soup)
    if movil:
        latitud = None
        longitud = None

    return ParsedSucursal(
        biblioteca_codigo=biblioteca_codigo,
        sucursal_codigo=sucursal_codigo,
        nombre=nombre,
        municipio=municipio,
        direccion=direccion,
        codigo_postal=codigo_postal,
        latitud=latitud,
        longitud=longitud,
        tipo_biblioteca=tipo_biblioteca,
        movil=movil,
    )


class DirectoryClient:
    """Cliente del Directorio de Bibliotecas de la Comunidad de Madrid."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        delay: float = 1.0,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or f"{settings.opac_base_url.rstrip('/')}{DIRECTORY_PATH}"
        ).rstrip("/")
        self.delay = max(0.0, delay)
        self._own_client = client is None
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": settings.user_agent},
        )
        self._last_request_at: float | None = None

    @classmethod
    def from_fuente(cls, fuente: Fuente, **kwargs) -> DirectoryClient:
        profile = FuenteProfile.from_model(fuente)
        path = directory_path(fuente)
        if not path:
            raise DirectoryUnavailable(
                f"La fuente {fuente.codigo} no tiene directorio configurado"
            )
        return cls(
            base_url=profile.base_url.rstrip("/") + str(path),
            delay=profile.delay,
            **kwargs,
        )

    def __enter__(self) -> DirectoryClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._own_client:
            self.client.close()

    def _wait(self) -> None:
        if self.delay <= 0 or self._last_request_at is None:
            return
        remaining = self.delay - (time.monotonic() - self._last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    @retry(
        retry=retry_if_exception_type((_TransientDirectoryError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        reraise=True,
    )
    def _get(self, path: str) -> str:
        self._wait()
        response = self.client.get(path)
        self._last_request_at = time.monotonic()
        if response.status_code >= 500:
            raise _TransientDirectoryError(
                f"Error temporal {response.status_code} en {path}"
            )
        response.raise_for_status()
        return response.text

    def fetch_list_page(self, posicion: int | None = None) -> str:
        path = "registros.cmd" if posicion is None else f"registros.cmd?posicion={posicion}"
        return self._get(path)

    def fetch_record(self, record_id: str) -> str:
        return self._get(f"registro.cmd?id={record_id}")

    def iter_record_ids(self, *, max_pages: int | None = None) -> Iterator[str]:
        first_page = self.fetch_list_page()
        pages = [first_page]
        positions = parse_directory_positions(first_page)
        if max_pages is not None:
            positions = positions[: max(0, max_pages - 1)]
        for position in positions:
            pages.append(self.fetch_list_page(position))
        seen: set[str] = set()
        for page in pages:
            for record_id in parse_directory_list(page):
                if record_id not in seen:
                    seen.add(record_id)
                    yield record_id

    def iter_records(
        self, *, limit: int | None = None, max_pages: int | None = None
    ) -> Iterator[ParsedSucursal | None]:
        for index, record_id in enumerate(self.iter_record_ids(max_pages=max_pages)):
            if limit is not None and index >= limit:
                break
            try:
                yield parse_directory_record(self.fetch_record(record_id))
            except Exception as exc:  # noqa: BLE001
                logger.warning("No se pudo procesar la ficha %s: %s", record_id, exc)
                yield None


def refresh_sucursales(
    session: Session,
    client: DirectoryClient,
    *,
    fuente: Fuente,
    limit: int | None = None,
    max_pages: int | None = None,
    only_known: bool = False,
) -> RefreshStats:
    """Actualiza las sucursales desde el directorio y devuelve la cobertura.

    Con ``only_known=True`` solo se procesan fichas de bibliotecas que ya
    existen en el catalogo. Se crean o actualizan sus sucursales, pero nunca se
    crean bibliotecas nuevas: las fichas de bibliotecas desconocidas se omiten.
    """
    stats = RefreshStats()
    known_libraries: set[str] | None = None
    if only_known:
        known_libraries = set(
            session.scalars(
                select(Biblioteca.codigo).where(Biblioteca.fuente_id == fuente.id)
            )
        )

    for parsed in client.iter_records(limit=limit, max_pages=max_pages):
        stats.records += 1
        if parsed is None:
            stats.omitted += 1
            continue

        stats.with_subc += 1
        if parsed.codigo_postal:
            stats.with_postal_code += 1
        if parsed.latitud is not None and parsed.longitud is not None:
            stats.with_coordinates += 1
        if parsed.movil:
            stats.mobile += 1

        if (
            known_libraries is not None
            and parsed.biblioteca_codigo not in known_libraries
        ):
            stats.omitted += 1
            continue

        biblioteca = session.scalars(
            select(Biblioteca).where(
                Biblioteca.fuente_id == fuente.id,
                Biblioteca.codigo == parsed.biblioteca_codigo,
            )
        ).first()
        if biblioteca is None:
            stats.omitted += 1
            logger.warning(
                "Biblioteca desconocida para SUBC %s/%s",
                parsed.biblioteca_codigo,
                parsed.sucursal_codigo or "",
            )
            continue

        if parsed.sucursal_codigo is None:
            update_biblioteca_location(session, biblioteca, parsed)
            stats.libraries_updated += 1
        else:
            upsert_sucursal(session, biblioteca, parsed)
            stats.branches_matched += 1

    session.flush()
    return stats
