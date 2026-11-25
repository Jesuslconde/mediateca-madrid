from __future__ import annotations

import time
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from mediateca_shared.constants import ENRICH_STATUSES, JOB_TYPES, TMDB_STATUSES
from mediateca_shared.models import Edicion, Obra
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mediateca.api.routers.ingest import router as ingest_router
from mediateca.catalog.fuentes import (
    FuenteNotFound,
    enabled_fuentes,
    get_fuente,
    list_fuentes,
)
from mediateca.catalog.grouping import (
    create_obra_and_group,
    group_editions_into_obra,
    ungroup_edition,
)
from mediateca.catalog.indexer import MeiliIndexer
from mediateca.catalog.jobs import (
    JobAlreadyActive,
    build_tmdb_client,
    enqueue_branches_job,
    enqueue_discover_job,
    enqueue_enrich_job,
    enqueue_index_job,
    enqueue_tmdb_job,
    has_active_job,
    ingest_metrics,
)
from mediateca.catalog.repository import (
    apply_tmdb_enrichment,
    count_pending_titns,
    record_tmdb_outcome,
)
from mediateca.catalog.tmdb import (
    TmdbAuthError,
    TmdbError,
    TmdbNotFoundError,
    build_movie_url,
    build_poster_url,
    resolve_countries,
)
from mediateca.core.config import settings
from mediateca.core.config_store import (
    FLARESOLVERR_URL_KEY,
    TMDB_API_TOKEN_KEY,
    TMDB_MAX_MATCH_ATTEMPTS_KEY,
    WORKER_CONCURRENCY_KEY,
    ConfigValidationError,
    effective_tmdb_api_token,
    effective_worker_concurrency,
    normalize_flaresolverr_url,
    normalize_tmdb_api_token,
    normalize_tmdb_max_match_attempts,
    normalize_worker_concurrency,
    set_config_value,
)
from mediateca.core.db import get_session_factory
from mediateca.core.logging import elapsed_ms, get_logger
from mediateca.core.scheduling import (
    ScheduleSettings,
    ScheduleValidationError,
    build_schedule_status,
    load_schedule_settings,
    save_schedule_settings,
)

from .agrupacion_queries import (
    AgrupacionFilter,
    agrupacion_rows,
    agrupacion_summary,
    agrupacion_total,
    obra_candidates,
)
from .catalog_queries import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    CatalogFilter,
    catalog_rows,
    catalog_summary,
)
from .queries import (
    catalog_coverage,
    enrichment_percentage,
    flaresolverr_config,
    job_fuente_counts,
    job_status_counts,
    job_type_counts,
    recent_jobs,
    serialize_inicio,
    serialize_tareas,
    tmdb_config,
    worker_config,
    worker_health,
)

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

DEGRADED_MESSAGE = (
    "No se pudo leer el estado de la ingesta. "
    "Revisa la conexion con la base de datos y vuelve a intentarlo."
)

ADMIN_COOKIE = "mediateca_admin"
ADMIN_COOKIE_MAX_AGE = 8 * 60 * 60
NEXT_PATHS = {"/", "/catalogo", "/agrupacion", "/tareas", "/configuracion"}


def _has_write_access(request: Request) -> bool:
    token = settings.dashboard_admin_token
    if not token:
        return True
    provided = request.cookies.get(ADMIN_COOKIE) or request.headers.get("X-Admin-Token")
    return provided == token


def _safe_next(value: str | None, default: str = "/") -> str:
    candidate = (value or "").strip()
    return candidate if candidate in NEXT_PATHS else default


def _safe_catalog_next(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate == "/catalogo":
        return candidate
    if candidate.startswith("/catalogo?"):
        return candidate
    return "/catalogo"


def _safe_agrupacion_next(value: str | None) -> str:
    candidate = (value or "").strip()
    if candidate == "/agrupacion":
        return candidate
    if candidate.startswith("/agrupacion?"):
        return candidate
    return "/agrupacion"


def _redirect_with(
    path: str,
    *,
    message: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    params: dict[str, str] = {}
    if message:
        params["message"] = message
    if error:
        params["error"] = error
    if not params:
        return RedirectResponse(path, status_code=303)
    separator = "&" if "?" in path else "?"
    return RedirectResponse(f"{path}{separator}{urlencode(params)}", status_code=303)


def _admin_error(next_path: str | None = None) -> RedirectResponse:
    return _redirect_with(
        _safe_next(next_path),
        error="Token de administracion requerido o incorrecto",
    )


async def _form_values(request: Request) -> dict[str, list[str]]:
    body = (await request.body()).decode("utf-8")
    return parse_qs(body, keep_blank_values=True)


def _form_int(
    values: dict[str, list[str]], name: str, default: int
) -> int:
    raw = (values.get(name) or [str(default)])[0].strip()
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ScheduleValidationError(f"El campo {name} debe ser un numero") from exc


def _selected_fuentes(values: dict[str, list[str]]) -> list[str]:
    selected: list[str] = []
    for raw in values.get("fuente") or []:
        codigo = raw.strip()
        if codigo and codigo not in selected:
            selected.append(codigo)
    return selected


def get_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def _pool_status(session: Session) -> str | None:
    try:
        pool = session.get_bind().pool  # type: ignore[attr-defined]
        return pool.status()
    except Exception:  # noqa: BLE001
        return None


def _base_context(
    request: Request, section: str, *, refresh_seconds: int | None
) -> dict[str, Any]:
    return {
        "section": section,
        "refresh_seconds": refresh_seconds,
        "generated_at": datetime.now(UTC),
        "admin_required": bool(settings.dashboard_admin_token),
        "is_admin": _has_write_access(request),
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
    }


def _inicio_context(request: Request, session: Session) -> dict[str, Any]:
    cover = catalog_coverage(session)
    fuentes = enabled_fuentes(session)
    last_by_source: dict[str, Any] = {}
    for job in recent_jobs(session, limit=200):
        codigo = job.fuente_codigo
        if codigo and codigo not in last_by_source:
            last_by_source[codigo] = job
    fuentes_resumen = [
        {"fuente": fuente, "last_job": last_by_source.get(fuente.codigo)}
        for fuente in fuentes
    ]
    context = _base_context(
        request, "inicio", refresh_seconds=settings.dashboard_refresh_seconds
    )
    context.update(
        {
            "status_counts": job_status_counts(session),
            "type_counts": job_type_counts(session),
            "fuente_counts": job_fuente_counts(session),
            "fuentes": fuentes,
            "fuentes_resumen": fuentes_resumen,
            "coverage": cover,
            "enrichment_percent": enrichment_percentage(cover),
            "metrics": ingest_metrics(session, cover),
            "worker": worker_health(session),
        }
    )
    return context


def _tareas_context(request: Request, session: Session) -> dict[str, Any]:
    context = _base_context(
        request, "tareas", refresh_seconds=settings.dashboard_refresh_seconds
    )
    context.update(
        {
            "jobs": recent_jobs(session),
            "fuentes": enabled_fuentes(session),
            "fuentes_todas": list_fuentes(session),
            "active_jobs": {
                job_type: has_active_job(session, job_type) for job_type in JOB_TYPES
            },
            "worker_concurrency": effective_worker_concurrency(session),
        }
    )
    return context


def _configuracion_context(request: Request, session: Session) -> dict[str, Any]:
    schedule = load_schedule_settings(session)
    context = _base_context(request, "configuracion", refresh_seconds=None)
    context.update(
        {
            "schedule": schedule,
            "schedule_status": build_schedule_status(session, schedule),
            "pending_titns": count_pending_titns(session),
            "flaresolverr": flaresolverr_config(session),
            "tmdb": tmdb_config(session),
            "worker": worker_config(session),
        }
    )
    return context


def _parse_catalog_filter(request: Request) -> CatalogFilter:
    q = request.query_params

    def _int(name: str, default: int | None) -> int | None:
        raw = q.get(name)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    return CatalogFilter(
        enrich_status=q.get("enrich_status") or None,
        tmdb_status=q.get("tmdb_status") or None,
        missing=q.get("missing") or "incluir",
        texto=q.get("q") or None,
        soporte=q.get("soporte") or None,
        biblioteca=q.get("biblioteca") or None,
        anio_desde=_int("anio_desde", None),
        anio_hasta=_int("anio_hasta", None),
        idioma=q.get("idioma") or None,
        pais=q.get("pais") or None,
        fuente=q.get("fuente") or None,
        page=max(_int("page", 1) or 1, 1),
        limit=min(max(_int("limit", DEFAULT_LIMIT) or DEFAULT_LIMIT, 1), MAX_LIMIT),
    )


def _page_query(request: Request, page: int) -> str:
    params = [(key, value) for key, value in request.query_params.multi_items() if key != "page"]
    params.append(("page", str(page)))
    return urlencode(params)


def _catalog_next(request: Request) -> str:
    params = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key not in {"message", "error"}
    ]
    return f"/catalogo?{urlencode(params)}" if params else "/catalogo"


def _catalogo_context(request: Request, session: Session) -> dict[str, Any]:
    filtro = _parse_catalog_filter(request)
    summary = catalog_summary(session, filtro)
    rows = catalog_rows(session, filtro)
    page = filtro.page
    limit = filtro.limit
    pages = max(1, (summary.total + limit - 1) // limit) if summary.total > 0 else 1
    context = _base_context(request, "catalogo", refresh_seconds=None)
    context.update(
        {
            "filter": filtro,
            "summary": summary,
            "rows": rows,
            "page": page,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
            "prev_query": _page_query(request, page - 1),
            "next_query": _page_query(request, page + 1),
            "next_path": _catalog_next(request),
            "estados_enrich": ENRICH_STATUSES,
            "estados_tmdb": TMDB_STATUSES,
            "fuentes": enabled_fuentes(session),
            "tmdb_available": bool(effective_tmdb_api_token(session)),
        }
    )
    return context


def _parse_agrupacion_filter(request: Request) -> AgrupacionFilter:
    q = request.query_params

    def _int(name: str, default: int) -> int:
        raw = q.get(name)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    estado = q.get("estado") or None
    if estado not in {"sin_obra", "manual", "automatica"}:
        estado = None
    anio_raw = q.get("anio") or None
    anio: int | None = None
    if anio_raw:
        try:
            anio = int(anio_raw)
        except ValueError:
            anio = None
    return AgrupacionFilter(
        texto=q.get("q") or None,
        fuente=q.get("fuente") or None,
        soporte=q.get("soporte") or None,
        estado=estado,
        anio=anio,
        amplio=q.get("amplio") is not None,
        page=max(_int("page", 1), 1),
        limit=min(max(_int("limit", DEFAULT_LIMIT), 1), MAX_LIMIT),
    )


def _agrupacion_next(request: Request) -> str:
    params = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key not in {"message", "error"}
    ]
    return f"/agrupacion?{urlencode(params)}" if params else "/agrupacion"


def _pagination_items(page: int, pages: int, *, window: int = 2) -> list[int | None]:
    """Números de página a mostrar, con ``None`` como elipsis."""
    if pages <= 1:
        return []
    shown: set[int] = {1, pages, page}
    for delta in range(1, window + 1):
        if page - delta >= 1:
            shown.add(page - delta)
        if page + delta <= pages:
            shown.add(page + delta)
    items: list[int | None] = []
    previous: int | None = None
    for number in sorted(shown):
        if previous is not None and number - previous > 1:
            items.append(None)
        items.append(number)
        previous = number
    return items


def _pagination_context(
    request: Request, page: int, total: int, limit: int
) -> dict[str, Any]:
    pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    pagination = _pagination_items(page, pages)
    return {
        "page": page,
        "pages": pages,
        "pagination": pagination,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_query": _page_query(request, page - 1),
        "next_query": _page_query(request, page + 1),
        "page_queries": {p: _page_query(request, p) for p in pagination if p is not None},
    }


def _agrupacion_context(request: Request, session: Session) -> dict[str, Any]:
    started = time.monotonic()
    filtro = _parse_agrupacion_filter(request)
    pool = _pool_status(session)
    logger.info(
        "Agrupacion: inicio de la peticion (q=%r, fuente=%r, soporte=%r, estado=%r, anio=%r, amplio=%r, page=%s, limit=%s, pool=%s)",
        filtro.texto,
        filtro.fuente,
        filtro.soporte,
        filtro.estado,
        filtro.anio,
        filtro.amplio,
        filtro.page,
        filtro.limit,
        pool,
        extra={
            "step": "agrupacion.request.start",
            "path": request.url.path,
            "method": request.method,
            "page": filtro.page,
            "pool_status": pool,
        },
    )

    step = time.monotonic()
    logger.info(
        "Agrupacion: calculando resumen...",
        extra={"step": "agrupacion.context.summary.start"},
    )
    summary = agrupacion_summary(session, filtro)
    logger.info(
        "Agrupacion: resumen listo (total=%s, sin_obra=%s, manual=%s, automatica=%s) en %.1f ms",
        summary.total,
        summary.sin_obra,
        summary.manual,
        summary.automatica,
        elapsed_ms(step),
        extra={
            "step": "agrupacion.context.summary.done",
            "duration_ms": elapsed_ms(step),
            "rows": summary.total,
        },
    )

    step = time.monotonic()
    logger.info(
        "Agrupacion: calculando total...",
        extra={"step": "agrupacion.context.total.start"},
    )
    total = agrupacion_total(session, filtro)
    logger.info(
        "Agrupacion: total=%s en %.1f ms",
        total,
        elapsed_ms(step),
        extra={
            "step": "agrupacion.context.total.done",
            "duration_ms": elapsed_ms(step),
            "rows": total,
        },
    )

    step = time.monotonic()
    logger.info(
        "Agrupacion: cargando filas (pagina=%s, limit=%s)...",
        filtro.page,
        filtro.limit,
        extra={"step": "agrupacion.context.rows.start", "page": filtro.page},
    )
    rows = agrupacion_rows(session, filtro)
    logger.info(
        "Agrupacion: %s filas cargadas en %.1f ms",
        len(rows),
        elapsed_ms(step),
        extra={
            "step": "agrupacion.context.rows.done",
            "duration_ms": elapsed_ms(step),
            "rows": len(rows),
            "page": filtro.page,
        },
    )

    step = time.monotonic()
    logger.info(
        "Agrupacion: buscando obras candidatas para %r...",
        filtro.texto,
        extra={"step": "agrupacion.context.candidates.start"},
    )
    candidates = obra_candidates(session, filtro.texto)
    logger.info(
        "Agrupacion: %s candidatas en %.1f ms",
        len(candidates),
        elapsed_ms(step),
        extra={
            "step": "agrupacion.context.candidates.done",
            "duration_ms": elapsed_ms(step),
            "rows": len(candidates),
        },
    )

    step = time.monotonic()
    logger.info(
        "Agrupacion: cargando fuentes...",
        extra={"step": "agrupacion.context.fuentes.start"},
    )
    fuentes = enabled_fuentes(session)
    logger.info(
        "Agrupacion: %s fuentes en %.1f ms",
        len(fuentes),
        elapsed_ms(step),
        extra={
            "step": "agrupacion.context.fuentes.done",
            "duration_ms": elapsed_ms(step),
            "rows": len(fuentes),
        },
    )

    page = filtro.page
    limit = filtro.limit
    context = _base_context(request, "agrupacion", refresh_seconds=None)
    context.update(
        {
            "filter": filtro,
            "summary": summary,
            "total": total,
            "rows": rows,
            "next_path": _agrupacion_next(request),
            "candidates": candidates,
            "fuentes": fuentes,
        }
    )
    context.update(_pagination_context(request, page, total, limit))
    pages = context["pages"]
    logger.info(
        "Agrupacion: contexto listo en %.1f ms (filas=%s, paginas=%s)",
        elapsed_ms(started),
        len(rows),
        pages,
        extra={
            "step": "agrupacion.context.done",
            "duration_ms": elapsed_ms(started),
            "rows": len(rows),
            "page": page,
        },
    )
    return context


def _agrupacion_ediciones_context(request: Request, session: Session) -> dict[str, Any]:
    filtro = _parse_agrupacion_filter(request)
    total = agrupacion_total(session, filtro)
    rows = agrupacion_rows(session, filtro)
    context: dict[str, Any] = {
        "filter": filtro,
        "total": total,
        "rows": rows,
        "next_path": _agrupacion_next(request),
    }
    context.update(_pagination_context(request, filtro.page, total, filtro.limit))
    return context


def _form_records(values: dict[str, list[str]]) -> list[str]:
    unique: list[str] = []
    for raw in values.get("record_id") or []:
        record_id = raw.strip()
        if record_id and record_id not in unique:
            unique.append(record_id)
    return unique


def _load_ediciones(session: Session, record_ids: list[str]) -> list[Edicion]:
    if not record_ids:
        raise ValueError("No hay ediciones seleccionadas")
    ediciones = list(
        session.scalars(select(Edicion).where(Edicion.record_id.in_(record_ids)))
    )
    if len(ediciones) != len(record_ids):
        raise ValueError("Alguna edicion seleccionada no existe")
    by_id = {edicion.record_id: edicion for edicion in ediciones}
    return [by_id[record_id] for record_id in record_ids]


def _reindex_grouping(session: Session, record_ids: list[str]) -> str | None:
    if not record_ids:
        return None
    try:
        MeiliIndexer().index_titns(session, record_ids)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudieron reindexar las ediciones agrupadas: %s", exc)
        return "Agrupacion guardada, pero no se pudo actualizar el indice; ejecuta make index"
    return None


def _degraded(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="degraded.html",
        context={
            "message": DEGRADED_MESSAGE,
            "refresh_seconds": settings.dashboard_refresh_seconds,
            "generated_at": datetime.now(UTC),
        },
    )


app = FastAPI(
    title="Mediateca Madrid - Estado de la ingesta",
    description="Vista de estado y API de observabilidad de la ingesta.",
)
app.include_router(ingest_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    try:
        context = _inicio_context(request, session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer el estado de la ingesta")
        return _degraded(request)
    return templates.TemplateResponse(
        request=request,
        name="inicio.html",
        context=context,
    )


@app.get("/api/dashboard/inicio")
def api_dashboard_inicio(session: Session = Depends(get_session)) -> dict[str, Any]:
    try:
        return serialize_inicio(session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer el estado de la ingesta")
        return {"status": "degraded", "message": DEGRADED_MESSAGE}


@app.get("/api/dashboard/tareas")
def api_dashboard_tareas(session: Session = Depends(get_session)) -> dict[str, Any]:
    try:
        return serialize_tareas(session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer los trabajos de la ingesta")
        return {"status": "degraded", "message": DEGRADED_MESSAGE}


@app.get("/tareas", response_class=HTMLResponse)
def tareas(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    try:
        context = _tareas_context(request, session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer los trabajos de la ingesta")
        return _degraded(request)
    return templates.TemplateResponse(
        request=request,
        name="tareas.html",
        context=context,
    )


@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    try:
        context = _catalogo_context(request, session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer el catalogo")
        return _degraded(request)
    return templates.TemplateResponse(
        request=request,
        name="catalogo.html",
        context=context,
    )


@app.get("/agrupacion", response_class=HTMLResponse)
def agrupacion(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    started = time.monotonic()
    try:
        context = _agrupacion_context(request, session)
    except SQLAlchemyError:
        logger.exception(
            "No se pudo leer la agrupacion manual",
            extra={
                "step": "agrupacion.error",
                "duration_ms": elapsed_ms(started),
            },
        )
        return _degraded(request)

    logger.info(
        "Agrupacion: renderizando plantilla con %s filas...",
        len(context["rows"]),
        extra={"step": "agrupacion.render.start", "rows": len(context["rows"])},
    )
    render_started = time.monotonic()
    response = templates.TemplateResponse(
        request=request,
        name="agrupacion.html",
        context=context,
    )
    logger.info(
        "Agrupacion: plantilla renderizada en %.1f ms",
        elapsed_ms(render_started),
        extra={
            "step": "agrupacion.render.done",
            "duration_ms": elapsed_ms(render_started),
            "rows": len(context["rows"]),
        },
    )
    logger.info(
        "Agrupacion: peticion completada en %.1f ms",
        elapsed_ms(started),
        extra={
            "step": "agrupacion.request.done",
            "duration_ms": elapsed_ms(started),
            "status_code": 200,
            "rows": len(context["rows"]),
        },
    )
    return response


@app.get("/agrupacion/ediciones", response_class=HTMLResponse)
def agrupacion_ediciones(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    try:
        context = _agrupacion_ediciones_context(request, session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer la agrupacion manual")
        return _degraded(request)
    return templates.TemplateResponse(
        request=request,
        name="agrupacion_ediciones.html",
        context=context,
    )


@app.post("/agrupacion/agrupar")
async def group_into_existing_obra(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_agrupacion_next((values.get("next") or [""])[0])
    if not _has_write_access(request):
        return _redirect_with(
            next_path,
            error="Token de administracion requerido o incorrecto",
        )

    try:
        obra_id = int((values.get("obra_id") or [""])[0].strip())
        if obra_id <= 0:
            raise ValueError
    except ValueError:
        return _redirect_with(next_path, error="Selecciona una obra destino valida")
    obra = session.get(Obra, obra_id)
    if obra is None:
        return _redirect_with(next_path, error="La obra destino no existe")

    record_ids = _form_records(values)
    try:
        ediciones = _load_ediciones(session, record_ids)
        affected = group_editions_into_obra(session, ediciones, obra)
        session.commit()
    except ValueError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo agrupar las ediciones")
        return _redirect_with(next_path, error="No se pudo guardar la agrupacion")

    warning = _reindex_grouping(session, affected)
    return _redirect_with(
        next_path,
        message=f"{len(affected)} ediciones agrupadas en {obra.titulo_uniforme}",
        error=warning,
    )


@app.post("/agrupacion/agrupar-nueva")
async def group_into_new_obra(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_agrupacion_next((values.get("next") or [""])[0])
    if not _has_write_access(request):
        return _redirect_with(
            next_path,
            error="Token de administracion requerido o incorrecto",
        )

    titulo = (values.get("titulo_uniforme") or [""])[0].strip()
    if not titulo:
        return _redirect_with(next_path, error="Introduce el titulo uniforme")
    raw_anio = (values.get("anio") or [""])[0].strip()
    try:
        anio = int(raw_anio) if raw_anio else None
    except ValueError:
        return _redirect_with(next_path, error="El anio debe ser un numero entero")

    record_ids = _form_records(values)
    try:
        ediciones = _load_ediciones(session, record_ids)
        obra, affected = create_obra_and_group(session, ediciones, titulo, anio)
        session.commit()
    except ValueError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo crear la obra y agrupar las ediciones")
        return _redirect_with(next_path, error="No se pudo guardar la agrupacion")

    warning = _reindex_grouping(session, affected)
    return _redirect_with(
        next_path,
        message=f"{len(affected)} ediciones agrupadas en {obra.titulo_uniforme}",
        error=warning,
    )


@app.post("/agrupacion/desvincular")
async def ungroup_from_obra(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_agrupacion_next((values.get("next") or [""])[0])
    if not _has_write_access(request):
        return _redirect_with(
            next_path,
            error="Token de administracion requerido o incorrecto",
        )

    record_ids = _form_records(values)
    try:
        ediciones = _load_ediciones(session, record_ids)
        affected = [ungroup_edition(session, edicion) for edicion in ediciones]
        session.commit()
    except ValueError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo desvincular las ediciones")
        return _redirect_with(next_path, error="No se pudo guardar la desvinculacion")

    warning = _reindex_grouping(session, affected)
    return _redirect_with(
        next_path,
        message=f"{len(affected)} ediciones devueltas a la agrupacion automatica",
        error=warning,
    )


@app.post("/catalogo/tmdb")
async def assign_manual_tmdb_id(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_catalog_next((values.get("next") or [""])[0])
    if not _has_write_access(request):
        return _redirect_with(
            next_path,
            error="Token de administracion requerido o incorrecto",
        )

    record_id = (values.get("record_id") or [""])[0].strip()
    raw_tmdb_id = (values.get("tmdb_id") or [""])[0].strip()
    try:
        tmdb_id = int(raw_tmdb_id)
        if tmdb_id <= 0:
            raise ValueError
    except ValueError:
        return _redirect_with(
            next_path,
            error="El ID de TMDB debe ser un numero entero positivo",
        )

    edicion = session.scalars(
        select(Edicion).where(Edicion.record_id == record_id)
    ).first()
    if edicion is None:
        return _redirect_with(next_path, error="No se encontro la edicion indicada")
    if edicion.tmdb_status != "unmatched":
        return _redirect_with(
            next_path,
            error="Solo se puede asignar un TMDB manual a una edicion unmatched",
        )

    client = build_tmdb_client(session, delay=0)
    if client is None:
        return _redirect_with(
            next_path,
            error="No hay token de TMDB configurado; guardalo en Configuracion",
        )

    try:
        with client:
            detail = client.get_movie(tmdb_id)
        apply_tmdb_enrichment(
            session,
            edicion,
            paises_origen=resolve_countries(detail),
            tmdb_id=detail.id,
            poster_url=build_poster_url(detail.poster_path),
            tmdb_url=build_movie_url(detail.id),
        )
        record_tmdb_outcome(session, edicion, "matched")
        session.commit()
    except TmdbNotFoundError:
        session.rollback()
        return _redirect_with(
            next_path,
            error=f"No existe la pelicula {tmdb_id} en TMDB",
        )
    except TmdbAuthError:
        session.rollback()
        return _redirect_with(
            next_path,
            error="El token de TMDB no es valido",
        )
    except TmdbError as exc:
        session.rollback()
        logger.warning("No se pudo validar el TMDB %s: %s", tmdb_id, exc)
        return _redirect_with(next_path, error=f"No se pudo consultar TMDB: {exc}")
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar el ID de TMDB manual")
        return _redirect_with(
            next_path,
            error="No se pudo guardar el ID de TMDB",
        )

    return _redirect_with(
        next_path,
        message=f"ID TMDB {detail.id} asignado a {edicion.titn}",
    )


@app.get("/configuracion", response_class=HTMLResponse)
def configuracion(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    try:
        context = _configuracion_context(request, session)
    except SQLAlchemyError:
        logger.exception("No se pudo leer la configuracion de la ingesta")
        return _degraded(request)
    return templates.TemplateResponse(
        request=request,
        name="configuracion.html",
        context=context,
    )


@app.post("/admin/login")
async def admin_login(
    request: Request,
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/")
    if not settings.dashboard_admin_token:
        return _redirect_with(
            next_path,
            error="No hay token de administracion configurado",
        )
    token = (values.get("token") or [""])[0].strip()
    if token != settings.dashboard_admin_token:
        return _admin_error(next_path)
    response = RedirectResponse(next_path, status_code=303)
    response.set_cookie(
        ADMIN_COOKIE,
        token,
        max_age=ADMIN_COOKIE_MAX_AGE,
        httponly=True,
        samesite="strict",
    )
    return response


@app.post("/admin/logout")
async def admin_logout(request: Request) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/")
    response = RedirectResponse(next_path, status_code=303)
    response.delete_cookie(ADMIN_COOKIE)
    return response


@app.post("/config/schedule")
async def save_schedule_config(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/configuracion")
    if not _has_write_access(request):
        return _admin_error(next_path)
    try:
        schedule = ScheduleSettings(
            enabled=(values.get("enabled") or ["false"])[0].lower()
            in {"1", "true", "on", "yes", "si", "sí"},
            discover_interval_hours=_form_int(values, "discover_interval_hours", 12),
            full_sweep_interval_hours=_form_int(
                values, "full_sweep_interval_hours", 168
            ),
            enrich_interval_hours=_form_int(values, "enrich_interval_hours", 12),
            enrich_batch_size=_form_int(values, "enrich_batch_size", 5000),
            index_interval_hours=_form_int(values, "index_interval_hours", 168),
            captcha_pause_minutes=_form_int(values, "captcha_pause_minutes", 30),
        )
        save_schedule_settings(session, schedule)
        session.commit()
    except ScheduleValidationError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar la programacion de ingesta")
        return _redirect_with(
            next_path,
            error="No se pudo guardar la programacion de ingesta",
        )
    return _redirect_with(next_path, message="Programacion guardada")


@app.post("/config/worker")
async def save_worker_config(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/configuracion")
    if not _has_write_access(request):
        return _admin_error(next_path)
    raw = (values.get("concurrency") or [""])[0]
    try:
        normalized = normalize_worker_concurrency(raw)
        if normalized is None:
            set_config_value(session, WORKER_CONCURRENCY_KEY, None)
            message = "Concurrencia eliminada; se usara la del entorno"
        else:
            set_config_value(session, WORKER_CONCURRENCY_KEY, str(normalized))
            message = f"Concurrencia guardada: {normalized}"
        session.commit()
    except ConfigValidationError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar la concurrencia del worker")
        return _redirect_with(
            next_path,
            error="No se pudo guardar la concurrencia del worker",
        )
    return _redirect_with(next_path, message=message)


@app.post("/jobs")
async def enqueue_job_from_dashboard(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/tareas")
    if not _has_write_access(request):
        return _admin_error(next_path)
    job_type = (values.get("job_type") or [""])[0].strip()
    fuente_codigo = (values.get("fuente") or ["madrid"])[0].strip() or "madrid"
    try:
        try:
            fuente = get_fuente(session, fuente_codigo)
        except Exception:
            from mediateca.catalog.fuentes import ensure_default_fuente

            if fuente_codigo != "madrid":
                raise
            fuente = ensure_default_fuente(session, fuente_codigo)
        if job_type == "discover":
            mode = (values.get("mode") or ["incremental"])[0].strip()
            job = enqueue_discover_job(
                session, fuente=fuente, mode=mode, reason="dashboard"
            )
        elif job_type == "enrich":
            limit = int((values.get("limit") or ["5000"])[0])
            if not 1 <= limit <= 50000:
                raise ValueError("El lote debe estar entre 1 y 50000")
            job = enqueue_enrich_job(
                session,
                fuente=fuente,
                batch_size=limit,
                since=None,
                reason="dashboard",
            )
        elif job_type == "index":
            job = enqueue_index_job(session, fuente=fuente)
        elif job_type == "branches":
            job = enqueue_branches_job(session, fuente=fuente, reason="dashboard")
        elif job_type == "tmdb":
            if not effective_tmdb_api_token(session):
                raise ValueError(
                    "No hay token de TMDB configurado; guardalo en Configuracion"
                )
            limit = int((values.get("limit") or ["5000"])[0])
            if not 1 <= limit <= 50000:
                raise ValueError("El lote debe estar entre 1 y 50000")
            refresh = (values.get("refresh") or ["false"])[0].lower() in {
                "1",
                "true",
                "on",
                "yes",
                "si",
                "sí",
            }
            job = enqueue_tmdb_job(
                session,
                fuente=fuente,
                batch_size=limit,
                refresh=refresh,
                reason="dashboard",
            )
        else:
            raise ValueError("Tipo de trabajo no valido")
        session.commit()
    except JobAlreadyActive as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except (ValueError, SQLAlchemyError) as exc:
        session.rollback()
        logger.exception("No se pudo encolar el trabajo desde el dashboard")
        return _redirect_with(next_path, error=str(exc))
    return _redirect_with(
        next_path,
        message=f"Trabajo {job.id} ({job.job_type}) encolado",
    )


BATCH_ACTIONS = {"discover", "discover_full", "enrich", "index"}


@app.post("/fuentes/estado")
async def update_fuente_estado(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/tareas")
    if not _has_write_access(request):
        return _admin_error(next_path)
    codigo = (values.get("fuente") or [""])[0].strip()
    accion = (values.get("accion") or [""])[0].strip()
    if accion not in {"habilitar", "deshabilitar"}:
        return _redirect_with(next_path, error="Accion no valida")
    enabled = accion == "habilitar"
    try:
        fuente = get_fuente(session, codigo)
        fuente.enabled = enabled
        session.commit()
    except FuenteNotFound as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo actualizar el estado de la fuente")
        return _redirect_with(
            next_path, error="No se pudo actualizar el estado de la fuente"
        )
    return _redirect_with(
        next_path,
        message=(
            f"Fuente {fuente.codigo} "
            f"{'habilitada' if enabled else 'deshabilitada'}"
        ),
    )


@app.post("/jobs/lote")
async def enqueue_batch_jobs(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/tareas")
    if not _has_write_access(request):
        return _admin_error(next_path)
    accion = (values.get("accion") or [""])[0].strip()
    if accion not in BATCH_ACTIONS:
        return _redirect_with(next_path, error="Accion no valida")
    codigos = _selected_fuentes(values)
    if not codigos:
        return _redirect_with(next_path, error="Selecciona al menos una fuente")
    limit = 5000
    if accion == "enrich":
        try:
            limit = int((values.get("limit") or ["5000"])[0])
        except (TypeError, ValueError):
            return _redirect_with(next_path, error="El lote debe ser un numero")
        if not 1 <= limit <= 50000:
            return _redirect_with(
                next_path, error="El lote debe estar entre 1 y 50000"
            )

    encolados: list[str] = []
    errores: list[str] = []
    for codigo in codigos:
        try:
            fuente = get_fuente(session, codigo)
            if not fuente.enabled:
                errores.append(f"{codigo}: deshabilitada")
                continue
            with session.begin_nested():
                if accion == "discover":
                    enqueue_discover_job(
                        session,
                        fuente=fuente,
                        mode="incremental",
                        reason="dashboard-lote",
                    )
                elif accion == "discover_full":
                    enqueue_discover_job(
                        session,
                        fuente=fuente,
                        mode="full",
                        reason="dashboard-lote",
                    )
                elif accion == "enrich":
                    enqueue_enrich_job(
                        session,
                        fuente=fuente,
                        batch_size=limit,
                        since=None,
                        reason="dashboard-lote",
                    )
                else:
                    enqueue_index_job(session, fuente=fuente)
            encolados.append(fuente.codigo)
        except JobAlreadyActive as exc:
            errores.append(f"{codigo}: {exc}")
        except (FuenteNotFound, ValueError) as exc:
            errores.append(f"{codigo}: {exc}")
        except SQLAlchemyError:
            logger.exception("No se pudo encolar un trabajo del lote")
            errores.append(f"{codigo}: error de base de datos")

    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudieron encolar los trabajos del lote")
        return _redirect_with(
            next_path, error="No se pudieron encolar los trabajos del lote"
        )

    if not encolados:
        return _redirect_with(
            next_path,
            error="; ".join(errores) or "No se encolo ningun trabajo",
        )
    return _redirect_with(
        next_path,
        message=f"{len(encolados)} trabajo(s) encolado(s): {', '.join(encolados)}",
        error="; ".join(errores) if errores else None,
    )


@app.post("/config/flaresolverr")
async def save_flaresolverr_config(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/configuracion")
    if not _has_write_access(request):
        return _admin_error(next_path)
    url = (values.get("url") or [""])[0]

    try:
        normalized = normalize_flaresolverr_url(url)
        set_config_value(session, FLARESOLVERR_URL_KEY, normalized)
        session.commit()
    except ConfigValidationError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar la configuracion de FlareSolverr")
        return _redirect_with(
            next_path,
            error="No se pudo guardar la configuracion de FlareSolverr",
        )

    message = (
        "Configuracion de FlareSolverr guardada"
        if normalized
        else "Configuracion de FlareSolverr eliminada"
    )
    return _redirect_with(next_path, message=message)


@app.post("/config/tmdb")
async def save_tmdb_config(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/configuracion")
    if not _has_write_access(request):
        return _admin_error(next_path)
    token = (values.get("token") or [""])[0]
    clear = (values.get("clear") or ["false"])[0].lower() in {
        "1",
        "true",
        "on",
        "yes",
        "si",
        "sí",
    }

    try:
        if clear:
            set_config_value(session, TMDB_API_TOKEN_KEY, None)
            message = "Configuracion de TMDB eliminada"
        else:
            normalized = normalize_tmdb_api_token(token)
            if normalized:
                set_config_value(session, TMDB_API_TOKEN_KEY, normalized)
                message = "Configuracion de TMDB guardada"
            else:
                message = "No se ha modificado la configuracion de TMDB"
        session.commit()
    except ConfigValidationError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar la configuracion de TMDB")
        return _redirect_with(
            next_path,
            error="No se pudo guardar la configuracion de TMDB",
        )

    return _redirect_with(next_path, message=message)


@app.post("/config/tmdb-attempts")
async def save_tmdb_attempts_config(
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    values = await _form_values(request)
    next_path = _safe_next((values.get("next") or [""])[0], "/configuracion")
    if not _has_write_access(request):
        return _admin_error(next_path)
    raw = (values.get("max_match_attempts") or [""])[0]

    try:
        normalized = normalize_tmdb_max_match_attempts(raw)
        if normalized is None:
            set_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY, None)
            message = "Limite de intentos de TMDB eliminado; se usara el del entorno"
        else:
            set_config_value(session, TMDB_MAX_MATCH_ATTEMPTS_KEY, str(normalized))
            message = f"Limite de intentos de TMDB guardado: {normalized}"
        session.commit()
    except ConfigValidationError as exc:
        session.rollback()
        return _redirect_with(next_path, error=str(exc))
    except SQLAlchemyError:
        session.rollback()
        logger.exception("No se pudo guardar el limite de intentos de TMDB")
        return _redirect_with(
            next_path,
            error="No se pudo guardar el limite de intentos de TMDB",
        )

    return _redirect_with(next_path, message=message)


@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("La base de datos no responde al healthcheck del dashboard")
        return {"status": "degraded", "db": "error"}
    return {"status": "ok", "db": "ok"}
