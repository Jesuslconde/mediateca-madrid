from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from mediateca_shared.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_ATTEMPTS,
    FINAL_STATUSES,
    JOB_CONFLICT_PAIRS,
    JOB_TYPES,
)
from mediateca_shared.models import Edicion, Fuente, HarvestJob
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, sessionmaker

from mediateca.catalog.fuentes import FuenteDisabled, require_enabled_fuente
from mediateca.core.config import settings
from mediateca.core.config_store import (
    effective_flaresolverr_url,
    effective_tmdb_api_token,
    effective_tmdb_max_match_attempts,
)
from mediateca.core.logging import get_logger
from mediateca.core.scheduling import last_completed_discover, load_schedule_settings

logger = get_logger(__name__)


@dataclass(slots=True)
class IngestCoverage:
    ediciones: int
    descubiertas: int
    enriquecidas: int
    pendientes: int
    fallidas: int
    trabajos_pendientes: int
    trabajos_en_ejecucion: int
    trabajos_completados: int
    trabajos_fallidos: int
    por_fuente: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass(slots=True)
class IngestMetrics:
    processed: int
    errors: int
    captchas: int
    captchas_solved: int
    captchas_failed: int
    session_renewals: int
    failed: int
    pending: int
    average_ms: float | None
    por_fuente: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass(slots=True)
class WorkerState:
    status: str
    last_heartbeat: datetime | None
    source: str | None


def _now() -> datetime:
    return datetime.now(UTC)


def create_job(
    session: Session,
    job_type: str,
    *,
    fuente: Fuente | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    cursor_doc: int | None = None,
    cursor_titn: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    stats: dict | None = None,
) -> HarvestJob:
    if job_type not in JOB_TYPES:
        raise ValueError(f"Tipo de trabajo no valido: {job_type}")

    if fuente is None and job_type != "index":
        fuente = _source_or_madrid(session, None)
    if fuente is not None and not fuente.enabled:
        raise FuenteDisabled(f"La fuente {fuente.codigo} esta deshabilitada")
    job_stats = dict(stats or {})
    if fuente is not None:
        job_stats.setdefault("fuente", fuente.codigo)
    job = HarvestJob(
        job_type=job_type,
        fuente_id=fuente.id if fuente is not None else None,
        status="pending",
        batch_size=batch_size,
        cursor_doc=cursor_doc,
        cursor_titn=cursor_titn,
        max_attempts=max_attempts,
        stats=job_stats,
    )
    session.add(job)
    session.flush()
    return job


class JobAlreadyActive(RuntimeError):
    pass


def active_job_types(
    session: Session, *, fuente_id: int | None = None
) -> set[str]:
    """Tipos de trabajo que estan ejecutandose ahora mismo."""
    stmt = select(HarvestJob.job_type).where(HarvestJob.status == "running")
    if fuente_id is not None:
        stmt = stmt.where(HarvestJob.fuente_id == fuente_id)
    return set(session.scalars(stmt))


def conflicting_job_types(job_type: str) -> set[str]:
    """Tipos que no pueden compartir worker con ``job_type``."""
    conflicting = {job_type}
    for left, right in JOB_CONFLICT_PAIRS:
        if left == job_type:
            conflicting.add(right)
        elif right == job_type:
            conflicting.add(left)
    return conflicting


def _running_jobs(session: Session) -> list[HarvestJob]:
    return list(
        session.scalars(
            select(HarvestJob).where(HarvestJob.status == "running")
        )
    )


def blocked_job_types(
    session: Session, *, fuente_id: int | None = None
) -> set[str]:
    """Tipos que no se pueden reclamar para una fuente."""
    blocked: set[str] = set()
    for job in _running_jobs(session):
        if job.job_type == "index" and job.fuente_id is None:
            return set(JOB_TYPES)
        if fuente_id is None or job.fuente_id == fuente_id:
            blocked.update(conflicting_job_types(job.job_type))
    return blocked


def has_active_job(
    session: Session, job_type: str, *, fuente_id: int | None = None
) -> bool:
    stmt = select(func.count(HarvestJob.id)).where(
        HarvestJob.job_type == job_type,
        HarvestJob.status.in_(("pending", "running")),
    )
    if fuente_id is not None:
        stmt = stmt.where(HarvestJob.fuente_id == fuente_id)
    return bool(session.scalar(stmt))


def enqueue_job(
    session: Session,
    job_type: str,
    *,
    fuente: Fuente | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    cursor_doc: int | None = None,
    cursor_titn: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    stats: dict | None = None,
    dedupe: bool = True,
) -> HarvestJob:
    if job_type not in JOB_TYPES:
        raise ValueError(f"Tipo de trabajo no valido: {job_type}")
    fuente_id = fuente.id if fuente is not None else None
    if dedupe and has_active_job(session, job_type, fuente_id=fuente_id):
        suffix = f" para la fuente '{fuente.codigo}'" if fuente is not None else ""
        raise JobAlreadyActive(
            f"Ya hay un trabajo de tipo '{job_type}' pendiente o en ejecucion{suffix}"
        )
    job = create_job(
        session,
        job_type,
        fuente=fuente,
        batch_size=batch_size,
        cursor_doc=cursor_doc,
        cursor_titn=cursor_titn,
        max_attempts=max_attempts,
        stats=stats,
    )
    session.flush()
    return job


def _source_or_madrid(session: Session, fuente: Fuente | None) -> Fuente:
    if fuente is not None:
        return fuente
    from mediateca.catalog.fuentes import ensure_default_fuente

    return ensure_default_fuente(session)


def enqueue_discover_job(
    session: Session,
    *,
    fuente: Fuente | None = None,
    mode: str = "incremental",
    batch_size: int = DEFAULT_BATCH_SIZE,
    reason: str = "manual",
) -> HarvestJob:
    if mode not in {"incremental", "full"}:
        raise ValueError("El modo de descubrimiento debe ser incremental o full")
    source = _source_or_madrid(session, fuente)
    cursor_doc: int | None = None
    cursor_titn: str | None = None
    if mode == "incremental":
        last = last_completed_discover(session, fuente_id=source.id)
        if last is None or (last.cursor_doc is None and last.cursor_titn is None):
            mode = "full"
        else:
            cursor_doc = last.cursor_doc
            cursor_titn = last.cursor_titn
    return enqueue_job(
        session,
        "discover",
        fuente=source,
        batch_size=batch_size,
        cursor_doc=cursor_doc,
        cursor_titn=cursor_titn,
        stats={"mode": mode, "reason": reason},
    )


def enqueue_enrich_job(
    session: Session,
    *,
    fuente: Fuente | None = None,
    since: datetime | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    reason: str = "manual",
    cursor_titn: str | None = None,
) -> HarvestJob:
    stats: dict[str, object] = {"reason": reason}
    if since is not None:
        stats["since"] = since.isoformat()
    return enqueue_job(
        session,
        "enrich",
        fuente=_source_or_madrid(session, fuente),
        batch_size=batch_size,
        cursor_titn=cursor_titn,
        stats=stats,
    )


def enqueue_index_job(
    session: Session, *, fuente: Fuente | None = None, global_: bool = False
) -> HarvestJob:
    if global_:
        return enqueue_job(session, "index", stats={"global": True, "reason": "manual"})
    source = _source_or_madrid(session, fuente)
    return enqueue_job(
        session,
        "index",
        fuente=source,
        stats={"reason": "manual", "fuente": source.codigo},
    )


def enqueue_tmdb_job(
    session: Session,
    *,
    fuente: Fuente | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    refresh: bool = False,
    reason: str = "manual",
) -> HarvestJob:
    return enqueue_job(
        session,
        "tmdb",
        fuente=_source_or_madrid(session, fuente),
        batch_size=batch_size,
        stats={"reason": reason, "refresh": refresh},
    )


def enqueue_branches_job(
    session: Session,
    *,
    fuente: Fuente | None = None,
    delay: float | None = None,
    max_pages: int | None = None,
    reason: str = "manual",
) -> HarvestJob:
    stats: dict[str, object] = {"reason": reason, "only_known": True}
    if delay is not None:
        stats["delay"] = delay
    if max_pages is not None:
        stats["max_pages"] = max_pages
    return enqueue_job(
        session, "branches", fuente=_source_or_madrid(session, fuente), stats=stats
    )


CLAIM_LOCK_SQL = (
    "SELECT pg_advisory_xact_lock(hashtext('mediateca:harvest_jobs:claim'))"
)


def _acquire_claim_lock(session: Session) -> None:
    """Serializa el reclamo para que no se cuelen trabajos incompatibles."""
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        session.execute(text(CLAIM_LOCK_SQL))


def claim_job(
    session: Session,
    *,
    job_types: tuple[str, ...] | list[str] | None = None,
    now: datetime | None = None,
) -> HarvestJob | None:
    _acquire_claim_lock(session)
    running = _running_jobs(session)
    if any(job.job_type == "index" and job.fuente_id is None for job in running):
        return None

    stmt = select(HarvestJob).where(HarvestJob.status == "pending")
    if job_types:
        stmt = stmt.where(HarvestJob.job_type.in_(list(job_types)))
    stmt = stmt.order_by(HarvestJob.created_at, HarvestJob.id).limit(100)

    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    job = None
    for candidate in session.scalars(stmt):
        if candidate.fuente_id is None:
            if candidate.job_type == "index" and not running:
                job = candidate
                break
            continue
        blocked = set()
        for active in running:
            if active.fuente_id == candidate.fuente_id:
                blocked.update(conflicting_job_types(active.job_type))
        if candidate.job_type not in blocked:
            job = candidate
            break
    if job is None:
        return None

    if job.fuente_id is not None:
        fuente = session.get(Fuente, job.fuente_id)
        now_value = now or _now()
        paused_until = fuente.paused_until if fuente is not None else None
        if paused_until is not None:
            if paused_until.tzinfo is None:
                paused_until = paused_until.replace(tzinfo=UTC)
            if paused_until > now_value:
                return None

    timestamp = now or _now()
    job.status = "running"
    job.started_at = timestamp
    job.heartbeat_at = timestamp
    job.attempts = (job.attempts or 0) + 1
    session.flush()
    return job


def touch_job(session: Session, job: HarvestJob, *, now: datetime | None = None) -> None:
    job.heartbeat_at = now or _now()
    session.flush()


def update_cursor(
    session: Session,
    job: HarvestJob,
    *,
    cursor_doc: int | None = None,
    cursor_titn: str | None = None,
    stats: dict | None = None,
) -> None:
    if cursor_doc is not None:
        job.cursor_doc = cursor_doc
    if cursor_titn is not None:
        job.cursor_titn = cursor_titn
    if stats is not None:
        job.stats = stats
    session.flush()


def finish_job(
    session: Session,
    job: HarvestJob,
    *,
    status: str = "completed",
    stats: dict | None = None,
    error: str | None = None,
    now: datetime | None = None,
) -> None:
    if status not in FINAL_STATUSES:
        raise ValueError(f"Estado final no valido: {status}")

    timestamp = now or _now()
    job.status = status
    job.finished_at = timestamp
    job.heartbeat_at = timestamp
    if stats is not None:
        job.stats = stats
    if error is not None:
        job.error = error
    session.flush()


def requeue_job(
    session: Session,
    job: HarvestJob,
    *,
    error: str | None = None,
    now: datetime | None = None,
) -> None:
    job.status = "pending"
    job.started_at = None
    job.heartbeat_at = now or _now()
    if error is not None:
        job.error = error
    session.flush()


def recover_stale_jobs(
    session: Session,
    *,
    stale_seconds: int | None = None,
    now: datetime | None = None,
) -> int:
    current = now or _now()
    stale = (
        stale_seconds
        if stale_seconds is not None
        else settings.worker_stale_seconds
    )
    cutoff = current - timedelta(seconds=stale)
    stmt = select(HarvestJob).where(
        HarvestJob.status == "running",
        or_(
            HarvestJob.heartbeat_at.is_(None),
            HarvestJob.heartbeat_at < cutoff,
        ),
    )
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    jobs = list(session.scalars(stmt))
    for job in jobs:
        if (job.attempts or 0) >= (job.max_attempts or 1):
            finish_job(
                session,
                job,
                status="failed",
                error="Heartbeat caducado; se agotaron los intentos",
                now=current,
            )
        else:
            requeue_job(
                session,
                job,
                error="Heartbeat caducado; trabajo reencolado",
                now=current,
            )
    if jobs:
        logger.warning("Trabajos estancados recuperados: %s", len(jobs))
    return len(jobs)


def create_stub(
    session: Session,
    titn: str,
    *,
    fuente: Fuente | None = None,
    seen_at: datetime | None = None,
) -> Edicion:
    from mediateca_shared.identity import compose_record_id

    source = _source_or_madrid(session, fuente)
    timestamp = seen_at or _now()
    record_id = compose_record_id(source.codigo, titn)
    edicion = session.scalars(
        select(Edicion).where(Edicion.record_id == record_id)
    ).first()
    if edicion is None:
        edicion = Edicion(
            fuente_id=source.id,
            record_id=record_id,
            titn=titn,
            titulo=titn,
            is_stub=True,
            discovery_seen_at=timestamp,
        )
        session.add(edicion)
        session.flush()
    elif edicion.discovery_seen_at is None:
        edicion.discovery_seen_at = timestamp
        session.flush()
    return edicion


def mark_enriched(
    session: Session,
    edicion: Edicion,
    *,
    fetched_at: datetime | None = None,
) -> None:
    edicion.detail_fetched_at = fetched_at or _now()
    edicion.is_stub = False
    edicion.missing_at = None
    session.flush()


def mark_missing(
    session: Session,
    edicion: Edicion,
    *,
    missing_at: datetime | None = None,
) -> None:
    edicion.missing_at = missing_at or _now()
    session.flush()


def coverage(session: Session) -> IngestCoverage:
    ediciones = session.scalar(select(func.count(Edicion.id))) or 0
    descubiertas = (
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.discovery_seen_at.is_not(None))
        )
        or 0
    )
    enriquecidas = (
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.detail_fetched_at.is_not(None))
        )
        or 0
    )
    pendientes = (
        session.scalar(
            select(func.count(Edicion.id)).where(
                or_(Edicion.is_stub.is_(True), Edicion.detail_fetched_at.is_(None))
            )
        )
        or 0
    )
    fallidas = (
        session.scalar(
            select(func.count(Edicion.id)).where(Edicion.missing_at.is_not(None))
        )
        or 0
    )

    jobs_by_status = dict(
        session.execute(
            select(HarvestJob.status, func.count(HarvestJob.id)).group_by(HarvestJob.status)
        ).all()
    )

    por_fuente: dict[str, dict[str, int]] = {}
    for fuente in session.scalars(select(Fuente).order_by(Fuente.codigo)):
        source_filter = Edicion.fuente_id == fuente.id
        por_fuente[fuente.codigo] = {
            "ediciones": int(
                session.scalar(
                    select(func.count(Edicion.id)).where(source_filter)
                )
                or 0
            ),
            "descubiertas": int(
                session.scalar(
                    select(func.count(Edicion.id)).where(
                        source_filter, Edicion.discovery_seen_at.is_not(None)
                    )
                )
                or 0
            ),
            "enriquecidas": int(
                session.scalar(
                    select(func.count(Edicion.id)).where(
                        source_filter, Edicion.detail_fetched_at.is_not(None)
                    )
                )
                or 0
            ),
            "pendientes": int(
                session.scalar(
                    select(func.count(Edicion.id)).where(
                        source_filter,
                        or_(
                            Edicion.is_stub.is_(True),
                            Edicion.detail_fetched_at.is_(None),
                        ),
                    )
                )
                or 0
            ),
            "fallidas": int(
                session.scalar(
                    select(func.count(Edicion.id)).where(
                        source_filter, Edicion.missing_at.is_not(None)
                    )
                )
                or 0
            ),
        }

    return IngestCoverage(
        ediciones=ediciones,
        descubiertas=descubiertas,
        enriquecidas=enriquecidas,
        pendientes=pendientes,
        fallidas=fallidas,
        trabajos_pendientes=int(jobs_by_status.get("pending", 0)),
        trabajos_en_ejecucion=int(jobs_by_status.get("running", 0)),
        trabajos_completados=int(jobs_by_status.get("completed", 0)),
        trabajos_fallidos=int(jobs_by_status.get("failed", 0)),
        por_fuente=por_fuente,
    )


def recent_jobs(session: Session, limit: int = 20) -> list[HarvestJob]:
    stmt = (
        select(HarvestJob)
        .order_by(HarvestJob.created_at.desc(), HarvestJob.id.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def ingest_metrics(
    session: Session, cover: IngestCoverage | None = None
) -> IngestMetrics:
    cover = cover or coverage(session)
    processed = errors = captchas = captchas_solved = captchas_failed = 0
    session_renewals = failed = 0
    total_ms = 0.0
    timed_processed = 0

    for job in session.scalars(select(HarvestJob)):
        stats = job.stats or {}
        job_processed = int(stats.get("processed", 0) or 0)
        processed += job_processed
        errors += int(stats.get("errors", 0) or 0)
        captchas += int(stats.get("captchas", 0) or 0)
        captchas_solved += int(stats.get("captchas_solved", 0) or 0)
        captchas_failed += int(stats.get("captchas_failed", 0) or 0)
        session_renewals += int(stats.get("session_renewals", 0) or 0)
        failed += len(stats.get("failed") or [])
        if job_processed > 0 and job.started_at and job.finished_at:
            try:
                elapsed = (job.finished_at - job.started_at).total_seconds() * 1000
            except TypeError:
                continue
            total_ms += elapsed
            timed_processed += job_processed

    by_source: dict[str, dict[str, int]] = {}
    for fuente in session.scalars(select(Fuente).order_by(Fuente.codigo)):
        source_jobs = list(
            session.scalars(
                select(HarvestJob).where(HarvestJob.fuente_id == fuente.id)
            )
        )
        source_metrics = {
            "processed": 0,
            "errors": 0,
            "captchas": 0,
            "captchas_solved": 0,
            "captchas_failed": 0,
            "session_renewals": 0,
            "failed": 0,
        }
        for job in source_jobs:
            stats = job.stats or {}
            source_metrics["processed"] += int(stats.get("processed", 0) or 0)
            source_metrics["errors"] += int(stats.get("errors", 0) or 0)
            source_metrics["captchas"] += int(stats.get("captchas", 0) or 0)
            source_metrics["captchas_solved"] += int(
                stats.get("captchas_solved", 0) or 0
            )
            source_metrics["captchas_failed"] += int(
                stats.get("captchas_failed", 0) or 0
            )
            source_metrics["session_renewals"] += int(
                stats.get("session_renewals", 0) or 0
            )
            source_metrics["failed"] += len(stats.get("failed") or [])
        by_source[fuente.codigo] = source_metrics

    return IngestMetrics(
        processed=processed,
        errors=errors,
        captchas=captchas,
        captchas_solved=captchas_solved,
        captchas_failed=captchas_failed,
        session_renewals=session_renewals,
        failed=failed,
        pending=cover.pendientes,
        average_ms=round(total_ms / timed_processed, 2) if timed_processed else None,
        por_fuente=by_source,
    )


def worker_state(
    session: Session,
    *,
    now: datetime | None = None,
    heartbeat_file: Path | None = None,
    stale_seconds: int | None = None,
) -> WorkerState:
    path = heartbeat_file if heartbeat_file is not None else settings.worker_heartbeat_file
    stale = (
        stale_seconds
        if stale_seconds is not None
        else settings.dashboard_worker_stale_seconds
    )
    current = now or _now()

    last_heartbeat: datetime | None = None
    source: str | None = None
    try:
        modified = path.stat().st_mtime
    except OSError:
        pass
    else:
        last_heartbeat = datetime.fromtimestamp(modified, tz=UTC)
        source = "file"

    if last_heartbeat is None:
        db_heartbeat = session.scalar(
            select(func.max(HarvestJob.heartbeat_at)).where(
                HarvestJob.status == "running"
            )
        )
        if db_heartbeat is not None:
            last_heartbeat = (
                db_heartbeat
                if db_heartbeat.tzinfo is not None
                else db_heartbeat.replace(tzinfo=UTC)
            )
            source = "database"

    if last_heartbeat is None:
        return WorkerState(status="degraded", last_heartbeat=None, source=None)

    age = (current - last_heartbeat).total_seconds()
    status = "ok" if age <= stale else "degraded"
    return WorkerState(status=status, last_heartbeat=last_heartbeat, source=source)


def maybe_chain_enrich(session: Session, job: HarvestJob) -> None:
    """Encadena el siguiente lote de enriquecimiento tras completar uno con pendientes."""
    from mediateca.catalog.repository import count_pending_titns

    stats = dict(job.stats or {})
    chain = int(stats.get("drain_chain", 0) or 0)
    processed = int(stats.get("processed", 0) or 0)
    cursor = stats.get("cursor_titn")

    pending_total = count_pending_titns(session, fuente_id=job.fuente_id)
    pending_after_cursor = count_pending_titns(
        session, fuente_id=job.fuente_id, after_titn=cursor
    )

    next_cursor: str | None = None
    if not settings.enrich_drain_enabled or settings.enrich_drain_max_chain <= 0:
        stop_reason = "disabled"
    elif pending_total <= 0:
        stop_reason = "no_pending"
    elif chain >= settings.enrich_drain_max_chain:
        stop_reason = "max_chain"
    elif pending_after_cursor > 0:
        next_cursor = cursor
        stop_reason = "chain_forward"
    elif processed > 0:
        stop_reason = "chain_wrap"
    else:
        stop_reason = "no_progress"

    drained = False
    if stop_reason in ("chain_forward", "chain_wrap"):
        try:
            fuente = session.get(Fuente, job.fuente_id) if job.fuente_id else None
            enqueued = enqueue_enrich_job(
                session,
                fuente=fuente,
                since=None,
                batch_size=job.batch_size or DEFAULT_BATCH_SIZE,
                cursor_titn=next_cursor,
                reason="drain",
            )
            next_stats = dict(enqueued.stats or {})
            next_stats["drain_chain"] = chain + 1
            enqueued.stats = next_stats
            session.commit()
            drained = True
        except JobAlreadyActive:
            session.rollback()
            stop_reason = "already_active"
        except Exception:  # noqa: BLE001
            session.rollback()
            logger.exception(
                "No se pudo encolar el siguiente lote de enriquecimiento",
                extra={"job_id": job.id, "job_type": job.job_type},
            )
            stop_reason = "enqueue_error"

    stats["pending_after"] = pending_total
    stats["pending_after_cursor"] = pending_after_cursor
    stats["drain_chain"] = chain
    stats["drained"] = drained
    stats["stop_reason"] = stop_reason
    job.stats = stats
    session.commit()


JobHandler = Callable[[Session, HarvestJob], dict[str, Any] | None]


def _opac_client(fuente: Fuente, **kwargs):
    from mediateca.catalog.harvester import OpacClient

    factory = getattr(OpacClient, "from_fuente", None)
    if callable(factory):
        return factory(fuente, **kwargs)
    try:
        return OpacClient(**kwargs)
    except TypeError:
        return OpacClient()


def _make_harvester(session: Session, **kwargs):
    from mediateca.catalog.harvester import Harvester

    try:
        return Harvester(session, **kwargs)
    except TypeError:
        return Harvester(session)


def _pending_index_titns(job: HarvestJob) -> list[str]:
    raw = (job.stats or {}).get("pending_index_titns") or []
    return [str(titn) for titn in raw]


def _index_titns_for_job(
    session: Session, job: HarvestJob, titns: list[str] | tuple[str, ...]
) -> int:
    from mediateca.catalog.indexer import MeiliIndexer

    targets = list(dict.fromkeys([*_pending_index_titns(job), *titns]))
    if not targets:
        return 0

    try:
        total = MeiliIndexer().index_titns(session, targets)
    except Exception:
        stats = dict(job.stats or {})
        stats["pending_index_titns"] = targets
        job.stats = stats
        session.commit()
        raise

    stats = dict(job.stats or {})
    stats.pop("pending_index_titns", None)
    job.stats = stats
    session.commit()
    return total


def _flush_pending_index(session: Session, job: HarvestJob) -> None:
    if _pending_index_titns(job):
        _index_titns_for_job(session, job, [])


def _index_handler(session: Session, job: HarvestJob) -> dict[str, Any]:
    from mediateca.catalog.indexer import MeiliIndexer

    total = MeiliIndexer().index_editions(
        session, reset=False, fuente_id=job.fuente_id
    )
    return {"indexed": total}


def _enqueue_enrich_after_discover(
    session: Session, job: HarvestJob, stats: dict[str, Any]
) -> None:
    if int(stats.get("processed", 0) or 0) <= 0:
        return
    since = job.started_at or job.created_at
    schedule = load_schedule_settings(session)
    try:
        fuente = session.get(Fuente, job.fuente_id) if job.fuente_id else None
        enqueued = enqueue_enrich_job(
            session,
            fuente=fuente,
            since=since,
            batch_size=schedule.enrich_batch_size,
            reason="after_discover",
        )
        session.commit()
    except JobAlreadyActive:
        logger.info(
            "Ya hay un trabajo de enriquecimiento activo; no se encola otro",
            extra={"job_id": job.id, "job_type": job.job_type},
        )
    except Exception:  # noqa: BLE001
        session.rollback()
        logger.exception(
            "No se pudo encolar el enriquecimiento posterior al descubrimiento",
            extra={"job_id": job.id, "job_type": job.job_type},
        )
    else:
        logger.info(
            "Enriquecimiento encolado tras el descubrimiento",
            extra={
                "job_id": job.id,
                "job_type": job.job_type,
                "enqueued_job_id": enqueued.id,
                "since": since.isoformat() if since else None,
            },
        )


def _index_processed_after_failure(
    session: Session, job: HarvestJob, titns: list[str]
) -> None:
    if not titns:
        return
    try:
        _index_titns_for_job(session, job, titns)
    except Exception:  # noqa: BLE001
        session.rollback()
        logger.exception(
            "No se pudieron indexar las fichas procesadas antes del fallo",
            extra={"job_id": job.id, "job_type": job.job_type},
        )


def _discover_handler(session: Session, job: HarvestJob) -> dict[str, Any]:

    _flush_pending_index(session, job)
    fuente = require_enabled_fuente(
        session, session.get(Fuente, job.fuente_id).codigo if job.fuente_id else None
    )
    with _opac_client(
        fuente, flaresolverr_url=effective_flaresolverr_url(session)
    ) as client:
        harvester = _make_harvester(session, client=client)
        harvester.fuente = fuente
        try:
            stats = harvester.harvest_discovery(job=job)
        except Exception:
            _index_processed_after_failure(session, job, harvester.processed_titns)
            raise
    _index_titns_for_job(session, job, stats.get("processed_titns", []))
    _enqueue_enrich_after_discover(session, job, stats)
    return stats


def build_tmdb_client(session: Session, *, delay: float | None = None):
    from mediateca.catalog.tmdb import TmdbClient

    token = effective_tmdb_api_token(session)
    return TmdbClient(token, delay=delay) if token else None


def _enrich_handler(session: Session, job: HarvestJob) -> dict[str, Any]:

    _flush_pending_index(session, job)
    tmdb_client = build_tmdb_client(session)
    fuente = require_enabled_fuente(
        session, session.get(Fuente, job.fuente_id).codigo if job.fuente_id else None
    )
    try:
        with _opac_client(
            fuente, flaresolverr_url=effective_flaresolverr_url(session)
        ) as client:
            harvester = _make_harvester(
                session,
                client=client,
                tmdb_client=tmdb_client,
                tmdb_max_match_attempts=effective_tmdb_max_match_attempts(session),
            )
            harvester.fuente = fuente
            try:
                stats = harvester.harvest_enrichment(job=job)
            except Exception:
                _index_processed_after_failure(session, job, harvester.processed_titns)
                raise
    finally:
        if tmdb_client is not None:
            tmdb_client.close()
    _index_titns_for_job(session, job, stats.get("processed_titns", []))
    return stats


def _tmdb_handler(session: Session, job: HarvestJob) -> dict[str, Any]:
    from mediateca.catalog.tmdb import TmdbError

    _flush_pending_index(session, job)
    tmdb_client = build_tmdb_client(session)
    if tmdb_client is None:
        raise TmdbError("No hay token de TMDB configurado")
    fuente = require_enabled_fuente(
        session, session.get(Fuente, job.fuente_id).codigo if job.fuente_id else None
    )
    try:
        with _opac_client(
            fuente, flaresolverr_url=effective_flaresolverr_url(session)
        ) as client:
            harvester = _make_harvester(
                session,
                client=client,
                tmdb_client=tmdb_client,
                tmdb_max_match_attempts=effective_tmdb_max_match_attempts(session),
            )
            harvester.fuente = fuente
            stats = harvester.harvest_tmdb_enrichment(
                limit=job.batch_size or DEFAULT_BATCH_SIZE,
                delay=settings.tmdb_delay,
                refresh=bool((job.stats or {}).get("refresh")),
            )
    finally:
        tmdb_client.close()
    _index_titns_for_job(session, job, stats.get("processed_titns", []))
    return stats


def _branches_handler(session: Session, job: HarvestJob) -> dict[str, Any]:
    from mediateca.catalog.directory import (
        DirectoryUnavailable,
        build_directory_client,
        directory_mode,
        refresh_sucursales,
    )

    stats = dict(job.stats or {})
    delay = stats.get("delay")
    if delay is None:
        delay = settings.crawl_delay
    max_pages = stats.get("max_pages")

    fuente = require_enabled_fuente(
        session, session.get(Fuente, job.fuente_id).codigo if job.fuente_id else None
    )
    try:
        client = build_directory_client(fuente, delay=float(delay))
    except DirectoryUnavailable as exc:
        logger.info("Directorio no disponible", extra={"fuente": fuente.codigo})
        return {
            "fuente": fuente.codigo,
            "directory": False,
            "message": str(exc),
        }
    with client:
        create_missing = directory_mode(fuente) == "create"
        result = refresh_sucursales(
            session,
            client,
            fuente=fuente,
            max_pages=int(max_pages) if max_pages is not None else None,
            only_known=not create_missing,
            create_missing=create_missing,
        )
    return asdict(result)


DEFAULT_HANDLERS: dict[str, JobHandler] = {
    "discover": _discover_handler,
    "enrich": _enrich_handler,
    "index": _index_handler,
    "tmdb": _tmdb_handler,
    "branches": _branches_handler,
}


def execute_job(
    session: Session,
    job: HarvestJob,
    *,
    handlers: dict[str, JobHandler] | None = None,
) -> dict[str, Any]:
    registry = {**DEFAULT_HANDLERS, **(handlers or {})}
    handler = registry.get(job.job_type)
    if handler is None:
        raise NotImplementedError(
            f"No hay handler para el trabajo '{job.job_type}'. "
            "Se registrara en el cambio de descubrimiento o enriquecimiento."
        )
    return handler(session, job) or {}


def backoff_seconds(attempts: int) -> float:
    return min(5.0 * (2 ** max(0, attempts - 1)), 3600.0)


def _touch_heartbeat_file(path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(int(time.time())), encoding="utf-8")


def _heartbeat_loop(
    factory: sessionmaker[Session],
    job_id: int,
    interval: float,
    stop_event: threading.Event,
    heartbeat_file: Path | None,
) -> None:
    while not stop_event.wait(interval):
        try:
            with factory() as session:
                job = session.get(HarvestJob, job_id)
                if job is not None and job.status == "running":
                    touch_job(session, job)
                    session.commit()
            _touch_heartbeat_file(heartbeat_file)
        except Exception:  # noqa: BLE001
            # El heartbeat no debe tumbar el trabajo principal.
            continue


def _is_captcha_error(exc: Exception) -> bool:
    from mediateca.catalog.harvester import CaptchaRequired

    return isinstance(exc, CaptchaRequired)


def worker_tick(
    session: Session,
    *,
    handlers: dict[str, JobHandler] | None = None,
    heartbeat_seconds: float = 0.0,
    heartbeat_file: Path | None = None,
) -> tuple[HarvestJob | None, float]:
    recover_stale_jobs(session)
    job = claim_job(session)
    if job is None:
        session.commit()
        return None, 0.0

    job_id = job.id
    started_monotonic = time.monotonic()
    logger.info(
        "Trabajo reclamado",
        extra={
            "job_id": job.id,
            "job_type": job.job_type,
            "fuente": job.stats.get("fuente") if job.stats else None,
            "result": "running",
        },
    )
    session.commit()

    stop_event = threading.Event()
    heartbeat_thread: threading.Thread | None = None
    if heartbeat_seconds > 0:
        factory = sessionmaker(
            bind=session.get_bind(), expire_on_commit=False, future=True
        )
        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(factory, job_id, heartbeat_seconds, stop_event, heartbeat_file),
            daemon=True,
        )
        heartbeat_thread.start()

    try:
        stats = execute_job(session, job, handlers=handlers)
        finish_job(session, job, status="completed", stats=stats)
        session.commit()
        if job.job_type == "enrich":
            maybe_chain_enrich(session, job)
        logger.info(
            "Trabajo completado",
            extra={
                "job_id": job.id,
                "job_type": job.job_type,
                "result": "completed",
                "duration_ms": round(
                    (time.monotonic() - started_monotonic) * 1000, 2
                ),
            },
        )
        return job, 0.0
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        failed_job = session.get(HarvestJob, job_id)
        if failed_job is None:
            return None, 0.0
        duration_ms = round((time.monotonic() - started_monotonic) * 1000, 2)
        if _is_captcha_error(exc):
            failed_job.attempts = max(0, (failed_job.attempts or 1) - 1)
            requeue_job(session, failed_job, error=str(exc))
            pause_minutes = max(
                1, load_schedule_settings(session).captcha_pause_minutes
            )
            if failed_job.fuente_id is not None:
                fuente = session.get(Fuente, failed_job.fuente_id)
                if fuente is not None:
                    fuente.paused_until = _now() + timedelta(minutes=pause_minutes)
            session.commit()
            logger.warning(
                "Captcha detectado; pausando la ingesta",
                extra={
                    "job_id": failed_job.id,
                    "job_type": failed_job.job_type,
                    "result": "paused",
                    "duration_ms": duration_ms,
                    "pause_minutes": pause_minutes,
                    "error": str(exc),
                },
            )
            return failed_job, float(pause_minutes * 60)
        if (failed_job.attempts or 0) >= (failed_job.max_attempts or 1):
            finish_job(session, failed_job, status="failed", error=str(exc))
            session.commit()
            logger.error(
                "Trabajo fallido",
                extra={
                    "job_id": failed_job.id,
                    "job_type": failed_job.job_type,
                    "result": "failed",
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
            )
            return failed_job, 0.0
        requeue_job(session, failed_job, error=str(exc))
        session.commit()
        logger.warning(
            "Trabajo reprogramado",
            extra={
                "job_id": failed_job.id,
                "job_type": failed_job.job_type,
                "result": "retry",
                "duration_ms": duration_ms,
                "error": str(exc),
            },
        )
        return failed_job, backoff_seconds(failed_job.attempts)
    finally:
        stop_event.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=1.0)
        _touch_heartbeat_file(heartbeat_file)


def run_worker(
    session_factory: sessionmaker[Session],
    *,
    handlers: dict[str, JobHandler] | None = None,
    poll_seconds: float = 5.0,
    heartbeat_seconds: float = 30.0,
    heartbeat_file: Path | None = None,
    max_iterations: int | None = None,
    stop_event: threading.Event | None = None,
) -> int:
    processed = 0
    while stop_event is None or not stop_event.is_set():
        with session_factory() as session:
            job, backoff = worker_tick(
                session,
                handlers=handlers,
                heartbeat_seconds=heartbeat_seconds,
                heartbeat_file=heartbeat_file,
            )
        _touch_heartbeat_file(heartbeat_file)

        if job is not None:
            processed += 1
            if max_iterations is not None and processed >= max_iterations:
                break

        wait = backoff if backoff > 0 else poll_seconds
        if stop_event is not None:
            stop_event.wait(wait)
        else:
            time.sleep(wait)

    return processed
