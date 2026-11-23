from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup
from mediateca_shared.fuentes import FuenteProfile
from mediateca_shared.models import Biblioteca, Fuente, Sucursal
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from mediateca.catalog.parser import BS_PARSER, clean
from mediateca.catalog.repository import (
    normalize_name,
    update_biblioteca_location,
    upsert_sucursal,
)
from mediateca.core.config import settings
from mediateca.core.logging import get_logger

logger = get_logger(__name__)

DIRECTORY_PATH = "/directorio_publicacion/i18n/comunidades"
RECORD_LINK_RE = re.compile(r"registro\.cmd\?id=(\d+)")
POSITION_RE = re.compile(r"posicion=(\d+)")
SUBC_RE = re.compile(r"SUBC=([^&\"'\s]+)")
LL_RE = re.compile(r"[?&]ll=\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)")
Q_COORDS_RE = re.compile(
    r"[?&]q=\s*(-?\d+(?:\.\d+)?)[\s+]*,[\s+]*(-?\d+(?:\.\d+)?)"
)
MAPS_PLACE_RE = re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)")
MAPS_AT_RE = re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
CP_LINE_RE = re.compile(r"^(\d{5})\s+(.+?)(?:\s*\(([^)]+)\))?\s*$")
TIPO_RE = re.compile(r"Tipo biblioteca:\s*([^\n]+)")


class _TransientDirectoryError(httpx.HTTPError):
    pass


class DirectoryUnavailable(RuntimeError):
    pass


def directory_path(fuente: Fuente) -> str | None:
    profile = FuenteProfile.from_model(fuente)
    return (profile.options or {}).get("directory_path")


def directory_config(fuente: Fuente) -> dict[str, object]:
    """Devuelve la configuracion normalizada del directorio de una fuente.

    Si la fuente declara ``options.directory`` se devuelve tal cual; si solo
    declara ``options.directory_path`` se devuelve un directorio HTML. Si no
    declara directorio, se devuelve un diccionario vacio.
    """
    options = FuenteProfile.from_model(fuente).options or {}
    config = options.get("directory")
    if isinstance(config, dict) and config:
        return dict(config)
    path = options.get("directory_path")
    if path:
        return {"kind": "html", "path": path}
    return {}


def directory_mode(fuente: Fuente) -> str:
    """Política de recolección del directorio: ``create`` o ``match``."""
    config = directory_config(fuente)
    return "create" if config.get("mode") == "create" else "match"


def build_directory_client(
    fuente: Fuente, **kwargs: object
) -> DirectoryClient | OpenDataDirectoryClient:
    """Construye el cliente de directorio adecuado al tipo declarado."""
    config = directory_config(fuente)
    if config.get("kind") == "opendata":
        return OpenDataDirectoryClient.from_fuente(fuente, **kwargs)
    return DirectoryClient.from_fuente(fuente, **kwargs)


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
    branches_created: int = 0
    libraries_updated: int = 0
    libraries_created: int = 0
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
    hrefs = [
        str(anchor["href"])
        for anchor in soup.find_all("a", href=True)
        if any(
            token in str(anchor["href"])
            for token in ("maps.google", "google.com/maps", "maps.app.goo.gl")
        )
    ]
    for pattern in (LL_RE, Q_COORDS_RE, MAPS_PLACE_RE, MAPS_AT_RE):
        for href in hrefs:
            matches = pattern.findall(href)
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
    biblioteca_codigo = ""
    sucursal_codigo = None
    if subc:
        parts = [part.strip().upper() for part in subc.split("/") if part.strip()]
        if parts:
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
        params: dict[str, object] = {
            "base_url": profile.base_url.rstrip("/") + str(path),
            "delay": profile.delay,
        }
        params.update(kwargs)
        return cls(**params)

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
        response = self.client.get(path, follow_redirects=True)
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


def _text(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _extract_subc(catalogue: object) -> str | None:
    if not catalogue:
        return None
    match = SUBC_RE.search(str(catalogue))
    if not match:
        return None
    return unquote(match.group(1)).strip() or None


def _identity(subc: str | None, icms_id: object) -> tuple[str, str | None]:
    if subc:
        parts = [part.strip().upper() for part in subc.split("/") if part.strip()]
        if not parts:
            return "", None
        if len(parts) >= 2:
            return "/".join(parts[:-1]), "/".join(parts)
        return parts[0], None
    if icms_id:
        return str(icms_id), None
    return "", None


def _normalize_postcode(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        digits = str(int(value))
    else:
        digits = "".join(ch for ch in str(value) if ch.isdigit())
    if digits.isdigit() and len(digits) in (4, 5):
        return digits.zfill(5)
    return None


def _parse_coord(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _normalize_coords(
    latitude: object, longitude: object
) -> tuple[float | None, float | None]:
    lat = _parse_coord(latitude)
    lon = _parse_coord(longitude)
    if lat is None or lon is None:
        return None, None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None, None
    if lat == 0.0 and lon == 0.0:
        return None, None
    return lat, lon


def _is_mobile(nombre: str) -> bool:
    fold = nombre.casefold()
    return (
        "bibliobus" in fold
        or "bibliobús" in fold
        or "móvil" in fold
        or "movil" in fold
    )


def parse_opendata_record(
    item: object, *, unit_types: list[str] | None = None
) -> ParsedSucursal | None:
    """Convierte una unidad del directorio abierto en ParsedSucursal."""
    if not isinstance(item, dict):
        return None

    unit_type = item.get("unit_type_name")
    allowed = unit_types or ["Biblioteca"]
    if unit_type not in allowed:
        return None

    nombre = _text(item.get("name"))
    if not nombre:
        return None

    subc = _extract_subc(item.get("catalogue"))
    biblioteca_codigo, sucursal_codigo = _identity(subc, item.get("icmsId"))
    if not biblioteca_codigo:
        return None

    codigo_postal = _normalize_postcode(item.get("postcode"))
    latitud, longitud = _normalize_coords(item.get("latitude"), item.get("longitude"))
    movil = _is_mobile(nombre)
    if movil:
        latitud = None
        longitud = None

    return ParsedSucursal(
        biblioteca_codigo=biblioteca_codigo,
        sucursal_codigo=sucursal_codigo,
        nombre=nombre,
        municipio=_text(item.get("municipality_name")),
        direccion=_text(item.get("address_name")),
        codigo_postal=codigo_postal,
        latitud=latitud,
        longitud=longitud,
        tipo_biblioteca=_text(unit_type),
        movil=movil,
    )


class OpenDataDirectoryClient:
    """Cliente del directorio de datos abiertos servido por una API JSON."""

    def __init__(
        self,
        *,
        url: str,
        delay: float = 1.0,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
        unit_types: list[str] | None = None,
        format: str = "json",
    ) -> None:
        self.url = url.rstrip("/")
        self.delay = max(0.0, delay)
        self.unit_types = unit_types or ["Biblioteca"]
        self.format = format
        self._own_client = client is None
        self.client = client or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": settings.user_agent},
        )
        self._last_request_at: float | None = None

    @classmethod
    def from_fuente(cls, fuente: Fuente, **kwargs: object) -> OpenDataDirectoryClient:
        config = directory_config(fuente)
        if config.get("kind") != "opendata" or not config.get("url"):
            raise DirectoryUnavailable(
                f"La fuente {fuente.codigo} no tiene directorio opendata configurado"
            )
        profile = FuenteProfile.from_model(fuente)
        unit_types = config.get("unit_types")
        if isinstance(unit_types, list):
            unit_types = [str(t) for t in unit_types]
        else:
            unit_types = None
        params: dict[str, object] = {
            "url": str(config["url"]),
            "delay": profile.delay,
            "unit_types": unit_types,
            "format": str(config.get("format") or "json"),
        }
        params.update(kwargs)
        return cls(**params)

    def __enter__(self) -> OpenDataDirectoryClient:
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
    def _get_items(self) -> list[object]:
        self._wait()
        response = self.client.get(
            self.url, params={"format": self.format}, follow_redirects=True
        )
        self._last_request_at = time.monotonic()
        if response.status_code >= 500:
            raise _TransientDirectoryError(
                f"Error temporal {response.status_code} en {self.url}"
            )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            data = data.get("data") or data.get("items") or data.get("results") or []
        if not isinstance(data, list):
            raise DirectoryUnavailable(
                f"Respuesta inesperada del directorio {self.url}"
            )
        return data

    def iter_records(
        self, *, limit: int | None = None, max_pages: int | None = None
    ) -> Iterator[ParsedSucursal | None]:
        for index, item in enumerate(self._get_items()):
            if limit is not None and index >= limit:
                break
            yield parse_opendata_record(item, unit_types=self.unit_types)


def _match_biblioteca_by_name(
    parsed: ParsedSucursal,
    known_by_name: dict[str, list[Biblioteca]] | None,
) -> Biblioteca | None:
    if known_by_name is None or not parsed.nombre:
        return None
    candidates = known_by_name.get(normalize_name(parsed.nombre), [])
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None
    if parsed.municipio:
        target = normalize_name(parsed.municipio)
        filtered = [
            biblioteca
            for biblioteca in candidates
            if biblioteca.municipio
            and normalize_name(biblioteca.municipio) == target
        ]
        if len(filtered) == 1:
            return filtered[0]
        if filtered:
            candidates = filtered
    return candidates[0] if len(candidates) == 1 else None


def refresh_sucursales(
    session: Session,
    client: DirectoryClient,
    *,
    fuente: Fuente,
    limit: int | None = None,
    max_pages: int | None = None,
    only_known: bool = False,
    create_missing: bool = False,
) -> RefreshStats:
    """Actualiza las sucursales desde el directorio y devuelve la cobertura.

    Con ``only_known=True`` solo se procesan fichas de bibliotecas que ya
    existen en el catalogo. Con ``create_missing=True`` se crean las bibliotecas
    y sucursales que falten a partir del directorio.
    """
    stats = RefreshStats()
    known_libraries: set[str] | None = None
    known_by_name: dict[str, list[Biblioteca]] | None = None
    if only_known:
        bibliotecas = session.scalars(
            select(Biblioteca).where(Biblioteca.fuente_id == fuente.id)
        ).all()
        known_libraries = {biblioteca.codigo for biblioteca in bibliotecas}
        known_by_name = {}
        for biblioteca in bibliotecas:
            normalized = normalize_name(biblioteca.nombre or "")
            if normalized:
                known_by_name.setdefault(normalized, []).append(biblioteca)

    for parsed in client.iter_records(limit=limit, max_pages=max_pages):
        stats.records += 1
        if parsed is None:
            stats.omitted += 1
            continue

        if parsed.biblioteca_codigo:
            stats.with_subc += 1
        if parsed.codigo_postal:
            stats.with_postal_code += 1
        if parsed.latitud is not None and parsed.longitud is not None:
            stats.with_coordinates += 1
        if parsed.movil:
            stats.mobile += 1

        biblioteca: Biblioteca | None = None
        if parsed.biblioteca_codigo:
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
        else:
            biblioteca = _match_biblioteca_by_name(parsed, known_by_name)
            if biblioteca is None:
                stats.omitted += 1
                logger.debug(
                    "Biblioteca sin SUBC no reconocida por nombre: %s", parsed.nombre
                )
                continue

        created = False
        if biblioteca is None:
            if not create_missing:
                stats.omitted += 1
                logger.warning(
                    "Biblioteca desconocida para SUBC %s/%s",
                    parsed.biblioteca_codigo,
                    parsed.sucursal_codigo or "",
                )
                continue
            biblioteca = Biblioteca(
                fuente_id=fuente.id,
                codigo=parsed.biblioteca_codigo,
                nombre=parsed.municipio or parsed.nombre,
            )
            session.add(biblioteca)
            session.flush()
            stats.libraries_created += 1
            created = True

        if parsed.sucursal_codigo is None:
            update_biblioteca_location(session, biblioteca, parsed)
            if not created:
                stats.libraries_updated += 1
        else:
            exists = session.scalars(
                select(Sucursal.id).where(
                    Sucursal.fuente_id == fuente.id,
                    Sucursal.codigo == parsed.sucursal_codigo,
                )
            ).first()
            if exists is None:
                stats.branches_created += 1
            upsert_sucursal(session, biblioteca, parsed)
            stats.branches_matched += 1

    session.flush()
    return stats
