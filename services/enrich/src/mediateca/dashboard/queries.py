from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mediateca_shared.constants import (
    JOB_STATUSES,
    JOB_TYPES,
    MAX_WORKER_CONCURRENCY,
    MIN_WORKER_CONCURRENCY,
)
from mediateca_shared.models import Fuente, HarvestJob
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mediateca.catalog.jobs import (
    IngestCoverage,
    coverage,
    has_active_job,
    ingest_metrics,
)
from mediateca.core.config import settings
from mediateca.core.config_store import (
    FLARESOLVERR_URL_KEY,
    TMDB_API_TOKEN_KEY,
    ConfigValidationError,
    effective_worker_concurrency,
    get_config_value,
    normalize_flaresolverr_url,
    normalize_tmdb_api_token,
    normalize_worker_concurrency,
    saved_worker_concurrency,
)


@dataclass(slots=True)
class WorkerHealth:
    status: str
    last_heartbeat: datetime | None
    source: str | None


@dataclass(slots=True)
class FlareSolverrConfig:
    saved_url: str | None
    env_url: str | None
    effective_url: str | None
    source: str
    active: bool


@dataclass(slots=True)
class TmdbConfig:
    saved: bool
    env: bool
    effective: bool
    source: str
    masked_token: str | None
    active: bool


@dataclass(slots=True)
class WorkerConfig:
    saved_concurrency: int | None
    env_concurrency: int
    effective_concurrency: int
    source: str
    min_concurrency: int
    max_concurrency: int


def _normalize_or_none(value: str | None) -> str | None:
    try:
        return normalize_flaresolverr_url(value)
    except ConfigValidationError:
        return None


def flaresolverr_config(session: Session) -> FlareSolverrConfig:
    saved = _normalize_or_none(get_config_value(session, FLARESOLVERR_URL_KEY))
    env = _normalize_or_none(settings.flaresolverr_url)

    if saved:
        return FlareSolverrConfig(
            saved_url=saved,
            env_url=env,
            effective_url=saved,
            source="dashboard",
            active=True,
        )
    if env:
        return FlareSolverrConfig(
            saved_url=None,
            env_url=env,
            effective_url=env,
            source="entorno",
            active=True,
        )
    return FlareSolverrConfig(
        saved_url=None,
        env_url=None,
        effective_url=None,
        source="ninguno",
        active=False,
    )


def _normalize_tmdb(value: str | None) -> str | None:
    try:
        return normalize_tmdb_api_token(value)
    except ConfigValidationError:
        return None


def _mask_token(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def tmdb_config(session: Session) -> TmdbConfig:
    saved = _normalize_tmdb(get_config_value(session, TMDB_API_TOKEN_KEY))
    env = _normalize_tmdb(settings.tmdb_api_token)

    if saved:
        return TmdbConfig(
            saved=True,
            env=bool(env),
            effective=True,
            source="dashboard",
            masked_token=_mask_token(saved),
            active=True,
        )
    if env:
        return TmdbConfig(
            saved=False,
            env=True,
            effective=True,
            source="entorno",
            masked_token=_mask_token(env),
            active=True,
        )
    return TmdbConfig(
        saved=False,
        env=False,
        effective=False,
        source="ninguno",
        masked_token=None,
        active=False,
    )


def worker_config(session: Session) -> WorkerConfig:
    try:
        env_concurrency = normalize_worker_concurrency(settings.worker_concurrency)
    except ConfigValidationError:
        env_concurrency = None
    if env_concurrency is None:
        env_concurrency = MIN_WORKER_CONCURRENCY

    saved = saved_worker_concurrency(session)
    effective = effective_worker_concurrency(session)
    return WorkerConfig(
        saved_concurrency=saved,
        env_concurrency=env_concurrency,
        effective_concurrency=effective,
        source="dashboard" if saved is not None else "entorno",
        min_concurrency=MIN_WORKER_CONCURRENCY,
        max_concurrency=MAX_WORKER_CONCURRENCY,
    )


def job_status_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(HarvestJob.status, func.count(HarvestJob.id)).group_by(HarvestJob.status)
    ).all()
    counts = {status: 0 for status in JOB_STATUSES}
    for status, total in rows:
        counts[str(status)] = int(total)
    return counts


def job_type_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(HarvestJob.job_type, func.count(HarvestJob.id)).group_by(
            HarvestJob.job_type
        )
    ).all()
    counts = {job_type: 0 for job_type in JOB_TYPES}
    for job_type, total in rows:
        counts[str(job_type)] = int(total)
    return counts


def job_fuente_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(Fuente.codigo, func.count(HarvestJob.id))
        .join(Fuente, Fuente.id == HarvestJob.fuente_id)
        .group_by(Fuente.codigo)
    ).all()
    return {str(codigo): int(total) for codigo, total in rows}


def recent_jobs(session: Session, limit: int | None = None) -> list[HarvestJob]:
    limit = settings.dashboard_recent_limit if limit is None else limit
    stmt = (
        select(HarvestJob)
        .order_by(HarvestJob.created_at.desc(), HarvestJob.id.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def worker_health(
    session: Session,
    *,
    now: datetime | None = None,
    heartbeat_file: Path | None = None,
    stale_seconds: int | None = None,
) -> WorkerHealth:
    path = heartbeat_file if heartbeat_file is not None else settings.worker_heartbeat_file
    stale = (
        stale_seconds
        if stale_seconds is not None
        else settings.dashboard_worker_stale_seconds
    )
    current = now or datetime.now(UTC)

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
        return WorkerHealth(status="degraded", last_heartbeat=None, source=None)

    age = (current - last_heartbeat).total_seconds()
    status = "ok" if age <= stale else "degraded"
    return WorkerHealth(status=status, last_heartbeat=last_heartbeat, source=source)


def enrichment_percentage(cover: IngestCoverage) -> int:
    if cover.ediciones <= 0:
        return 0
    return round(cover.enriquecidas * 100 / cover.ediciones)


def catalog_coverage(session: Session) -> IngestCoverage:
    return coverage(session)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def serialize_worker(worker: WorkerHealth) -> dict[str, Any]:
    return {
        "status": worker.status,
        "last_heartbeat": _iso(worker.last_heartbeat),
        "source": worker.source,
    }


def serialize_job(job: HarvestJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "fuente": job.fuente_codigo or "global",
        "job_type": job.job_type,
        "status": job.status,
        "cursor_doc": job.cursor_doc,
        "cursor_titn": job.cursor_titn,
        "attempts": job.attempts or 0,
        "max_attempts": job.max_attempts or 0,
        "created_at": _iso(job.created_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "heartbeat_at": _iso(job.heartbeat_at),
        "error": job.error,
    }


def serialize_inicio(
    session: Session, *, now: datetime | None = None
) -> dict[str, Any]:
    cover = catalog_coverage(session)
    return {
        "worker": serialize_worker(worker_health(session, now=now)),
        "status_counts": job_status_counts(session),
        "type_counts": job_type_counts(session),
        "fuente_counts": job_fuente_counts(session),
        "coverage": asdict(cover),
        "enrichment_percent": enrichment_percentage(cover),
        "metrics": asdict(ingest_metrics(session, cover)),
        "generated_at": _iso(now or datetime.now(UTC)),
    }


def serialize_tareas(
    session: Session, *, now: datetime | None = None
) -> dict[str, Any]:
    return {
        "jobs": [serialize_job(job) for job in recent_jobs(session)],
        "active_jobs": {
            job_type: has_active_job(session, job_type) for job_type in JOB_TYPES
        },
        "worker_concurrency": effective_worker_concurrency(session),
        "generated_at": _iso(now or datetime.now(UTC)),
    }
