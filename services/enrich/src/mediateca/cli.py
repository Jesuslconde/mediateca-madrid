from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path

import typer
from mediateca_shared.constants import MAX_WORKER_CONCURRENCY
from mediateca_shared.lists import Lista
from mediateca_shared.models import Biblioteca, Edicion, Ejemplar, Fuente, HarvestJob
from mediateca_shared.version import SCHEMA_VERSION
from rich.console import Console
from rich.table import Table
from sqlalchemy import delete, func, select

from mediateca.catalog.calibration import CalibrationError, calibrate_source
from mediateca.catalog.directory import (
    DirectoryUnavailable,
    build_directory_client,
    directory_config,
    directory_mode,
    refresh_sucursales,
)
from mediateca.catalog.fuentes import get_fuente, require_enabled_fuente, seed_default_fuente
from mediateca.catalog.harvester import Harvester, OpacClient
from mediateca.catalog.indexer import MeiliIndexer
from mediateca.catalog.jobs import (
    DEFAULT_HANDLERS,
    JobAlreadyActive,
    build_tmdb_client,
    coverage,
    enqueue_branches_job,
    ingest_metrics,
    recent_jobs,
    run_worker,
    worker_state,
    worker_tick,
)
from mediateca.catalog.parser import parse_file
from mediateca.catalog.scheduler import enqueue_due_jobs, run_scheduler
from mediateca.catalog.title_backfill import backfill_titles
from mediateca.core.config import settings
from mediateca.core.config_store import (
    effective_flaresolverr_url,
    effective_tmdb_max_match_attempts,
    effective_worker_concurrency,
)
from mediateca.core.db import get_engine, get_session_factory, init_db, session_scope
from mediateca.core.logging import configure_logging, get_logger


def _opac_client(fuente, **kwargs):
    factory = getattr(OpacClient, "from_fuente", None)
    if callable(factory):
        return factory(fuente, **kwargs)
    try:
        return OpacClient(**kwargs)
    except TypeError:
        return OpacClient()


def _directory_client(fuente, **kwargs):
    return build_directory_client(fuente, **kwargs)


app = typer.Typer(
    name="mediateca",
    help="Catalogo alternativo de videos y DVD/Blu-ray de Madrid.",
    no_args_is_help=True,
)
console = Console()
logger = get_logger(__name__)


@app.command("init-db")
def init_db_command() -> None:
    """Crea las tablas y el indice de Meilisearch."""
    configure_logging()
    init_db()
    try:
        MeiliIndexer().ensure_index()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]No se pudo inicializar Meilisearch: {exc}[/yellow]")
    console.print("[green]Base de datos e indice inicializados[/green]")


def _apply_migrations() -> None:
    scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
    migrations = sorted(scripts_dir.glob("migrate_*.sql"))
    if not migrations:
        console.print(f"[red]No se encontraron migraciones en {scripts_dir}[/red]")
        raise typer.Exit(code=1)
    with get_engine().begin() as conn:
        Fuente.__table__.create(bind=conn, checkfirst=True)
        seed_default_fuente(conn)
        for migration in migrations:
            conn.exec_driver_sql(migration.read_text(encoding="utf-8"))
            console.print(f"[green]Migracion aplicada:[/green] {migration.name}")
        conn.exec_driver_sql(
            "INSERT INTO schema_meta (key, value) VALUES ('schema_version', %(v)s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            {"v": SCHEMA_VERSION},
        )


def _current_schema_version() -> str | None:
    try:
        with get_engine().connect() as conn:
            row = conn.exec_driver_sql(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).first()
    except Exception:  # noqa: BLE001
        return None
    return str(row[0]) if row is not None else None


@app.command("migrate")
def migrate_command() -> None:
    """Aplica las migraciones SQL idempotentes."""
    configure_logging()
    _apply_migrations()
    console.print("[green]Migraciones aplicadas[/green]")


@app.command("calibrate-source")
def calibrate_source_command(
    fuente: str = typer.Option(..., "--fuente", help="Codigo de fuente"),
    apply: bool = typer.Option(
        True, "--apply/--no-apply", help="Guardar el perfil calibrado en la fuente"
    ),
) -> None:
    """Calibra el patron de sesion y el codigo de video de una fuente."""
    configure_logging()
    with session_scope() as session:
        source = get_fuente(session, fuente)
        try:
            result = calibrate_source(source)
        except CalibrationError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        if apply:
            source.session_pattern = result.session_pattern
            source.format_value = result.format_value
            session.commit()

    table = Table(title=f"Calibracion de {fuente}")
    table.add_column("Campo")
    table.add_column("Valor")
    table.add_row("Patron de sesion", result.session_pattern)
    table.add_row("Formato de video", f"{result.format_value} ({result.format_label})")
    table.add_row("Sesion detectada", result.session_url)
    table.add_row("Aplicado", "si" if apply else "no")
    console.print(table)


@app.command("init")
def init_command() -> None:
    """Inicializa la base, aplica migraciones y reconstruye el indice si cambia la version."""
    configure_logging()
    previous = _current_schema_version()
    init_db()
    try:
        MeiliIndexer().ensure_index()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]No se pudo inicializar Meilisearch: {exc}[/yellow]")
    _apply_migrations()
    with session_scope() as session:
        session.execute(delete(Lista).where(Lista.expires_at < func.now()))
    reset = previous is None or int(previous) < int(SCHEMA_VERSION)
    with session_scope() as session:
        total = MeiliIndexer().index_editions(session, reset=reset)
    console.print(
        f"[green]Inicializacion completada:[/green] {total} ediciones indexadas "
        f"({'reset' if reset else 'sin reset'})"
    )


@app.command("clean-lists")
def clean_lists_command() -> None:
    """Elimina las listas de favoritos caducadas."""
    configure_logging()
    with session_scope() as session:
        result = session.execute(delete(Lista).where(Lista.expires_at < func.now()))
        deleted = result.rowcount or 0
    console.print(f"[green]Listas caducadas eliminadas:[/green] {deleted}")


@app.command("refresh-branches")
def refresh_branches_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
    delay: float = typer.Option(
        settings.crawl_delay, "--delay", min=0.0, help="Segundos entre peticiones"
    ),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Fichas maximas"),
    max_pages: int | None = typer.Option(
        None, "--max-pages", min=1, help="Paginas de listado maximas"
    ),
) -> None:
    """Actualiza direcciones y coordenadas de las sucursales desde el directorio."""
    configure_logging()
    with session_scope() as session:
        source = require_enabled_fuente(session, fuente)
        try:
            client = _directory_client(source, delay=delay)
        except DirectoryUnavailable as exc:
            console.print(f"[yellow]{exc}[/yellow]")
            return
        with client:
            create_missing = directory_mode(source) == "create"
            stats = refresh_sucursales(
                session,
                client,
                fuente=source,
                limit=limit,
                max_pages=max_pages,
                only_known=not create_missing,
                create_missing=create_missing,
            )

    table = Table(title="Actualizacion de sucursales")
    table.add_column("Metrica")
    table.add_column("Valor", justify="right")
    table.add_row("Fichas leidas", str(stats.records))
    table.add_row("Con SUBC", str(stats.with_subc))
    table.add_row("Con codigo postal", str(stats.with_postal_code))
    table.add_row("Con coordenadas", str(stats.with_coordinates))
    table.add_row("Sucursales emparejadas", str(stats.branches_matched))
    table.add_row("Sucursales creadas", str(stats.branches_created))
    table.add_row("Bibliotecas actualizadas", str(stats.libraries_updated))
    table.add_row("Bibliotecas creadas", str(stats.libraries_created))
    table.add_row("Bibliotecas moviles", str(stats.mobile))
    table.add_row("Omitidas", str(stats.omitted))
    console.print(table)


@app.command("enqueue-branches")
def enqueue_branches_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
) -> None:
    """Encola la recarga de direcciones de bibliotecas ya conocidas."""
    configure_logging()
    with session_scope() as session:
        try:
            source = require_enabled_fuente(session, fuente)
            if not directory_config(source):
                console.print(
                    f"[yellow]La fuente {source.codigo} no tiene directorio disponible[/yellow]"
                )
                return
            job = enqueue_branches_job(session, fuente=source, reason="cli")
        except JobAlreadyActive as exc:
            console.print(f"[yellow]{exc}[/yellow]")
            raise typer.Exit(code=1) from exc
        session.commit()
    console.print(
        f"[green]Trabajo {job.id} ({job.job_type}) encolado[/green]"
    )


@app.command("harvest")
def harvest_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
    query: str = typer.Option("cine", "--query", "-q", help="Termino de busqueda"),
    max_pages: int = typer.Option(1, "--max-pages", min=1, help="Paginas maximas"),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Fichas maximas"),
    delay: float = typer.Option(1.0, "--delay", min=0.1, help="Segundos entre peticiones"),
    index: bool = typer.Option(False, "--index", help="Indexar al terminar"),
) -> None:
    """Recolecta fichas del OPAC y las guarda en PostgreSQL."""
    configure_logging()
    with session_scope() as session:
        source = require_enabled_fuente(session, fuente)
        with _opac_client(
            source, delay=delay, flaresolverr_url=effective_flaresolverr_url(session)
        ) as client:
            harvester = Harvester(session, fuente=source, client=client)
            stats = harvester.harvest_query(
                query, max_pages=max_pages, limit=limit, delay=delay
            )
    console.print(f"[green]Recoleccion terminada:[/green] {stats}")
    if index:
        with session_scope() as session:
            total = MeiliIndexer().index_editions(session, reset=False)
        console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("discover")
def discover_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
    max_pages: int | None = typer.Option(
        None, "--max-pages", min=1, help="Paginas maximas (todas por defecto)"
    ),
    limit: int | None = typer.Option(None, "--limit", min=1, help="TITN maximos"),
    delay: float = typer.Option(1.0, "--delay", min=0.1, help="Segundos entre peticiones"),
    index: bool = typer.Option(False, "--index", help="Indexar al terminar"),
) -> None:
    """Descubre el catalogo completo y crea ediciones stub."""
    configure_logging()
    with session_scope() as session:
        source = require_enabled_fuente(session, fuente)
        with _opac_client(
            source, delay=delay, flaresolverr_url=effective_flaresolverr_url(session)
        ) as client:
            harvester = Harvester(session, fuente=source, client=client)
            stats = harvester.harvest_discovery(
                max_pages=max_pages, limit=limit, delay=delay
            )
    console.print(f"[green]Descubrimiento terminado:[/green] {stats}")
    if index:
        with session_scope() as session:
            total = MeiliIndexer().index_titns(
                session, stats.get("processed_titns", [])
            )
        console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("enrich")
def enrich_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
    limit: int = typer.Option(
        5000, "--limit", min=1, help="Fichas maximas por lote"
    ),
    delay: float = typer.Option(1.0, "--delay", min=0.1, help="Segundos entre peticiones"),
    index: bool = typer.Option(False, "--index", help="Indexar el lote al terminar"),
) -> None:
    """Enriquece por lotes las ediciones descubiertas y pendientes."""
    configure_logging()
    with session_scope() as session:
        source = require_enabled_fuente(session, fuente)
        tmdb_client = build_tmdb_client(session)
        try:
            with _opac_client(
                source, delay=delay, flaresolverr_url=effective_flaresolverr_url(session)
            ) as client:
                harvester = Harvester(
                    session,
                    fuente=source,
                    client=client,
                    tmdb_client=tmdb_client,
                    tmdb_max_match_attempts=effective_tmdb_max_match_attempts(session),
                )
                stats = harvester.harvest_enrichment(limit=limit, delay=delay)
        finally:
            if tmdb_client is not None:
                tmdb_client.close()
    console.print(f"[green]Enriquecimiento terminado:[/green] {stats}")
    if index:
        with session_scope() as session:
            total = MeiliIndexer().index_titns(
                session, stats.get("processed_titns", [])
            )
        console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("tmdb-enrich")
def tmdb_enrich_command(
    fuente: str = typer.Option("madrid", "--fuente", help="Codigo de fuente"),
    limit: int = typer.Option(
        5000, "--limit", min=1, help="Ediciones maximas por lote"
    ),
    delay: float = typer.Option(
        0.25, "--delay", min=0.0, help="Segundos entre peticiones a TMDB"
    ),
    no_index: bool = typer.Option(
        False, "--no-index", help="No indexar los TITN procesados"
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Reconsultar TMDB tambien para las ediciones ya sincronizadas",
    ),
) -> None:
    """Completa los metadatos TMDB de las ediciones ya enriquecidas."""
    configure_logging()
    with session_scope() as session:
        source = require_enabled_fuente(session, fuente)
        tmdb_client = build_tmdb_client(session, delay=delay)
        if tmdb_client is None:
            console.print(
                "[red]No hay token de TMDB configurado; "
                "guardalo en el dashboard o define MEDIATECA_TMDB_API_TOKEN[/red]"
            )
            raise typer.Exit(code=1)
        try:
            with _opac_client(source) as client:
                harvester = Harvester(
                    session,
                    fuente=source,
                    client=client,
                    tmdb_client=tmdb_client,
                    tmdb_max_match_attempts=effective_tmdb_max_match_attempts(session),
                )
                stats = harvester.harvest_tmdb_enrichment(
                    limit=limit, delay=delay, refresh=refresh
                )
        finally:
            tmdb_client.close()
    console.print(f"[green]Backfill TMDB terminado:[/green] {stats}")
    if not no_index and stats["processed_titns"]:
        with session_scope() as session:
            total = MeiliIndexer().index_titns(
                session, stats["processed_titns"]
            )
        console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("normalize-titles")
def normalize_titles_command(
    apply: bool = typer.Option(
        False, "--apply", help="Aplicar los titulos calculados en la base de datos"
    ),
    limit: int | None = typer.Option(
        None, "--limit", min=1, help="Numero maximo de ediciones"
    ),
    fuente: str | None = typer.Option(
        None, "--fuente", help="Limitar a una fuente por codigo, por ejemplo andalucia"
    ),
    material_only: bool = typer.Option(
        False,
        "--material-only",
        help="Limpiar solo calificadores de material del titulo actual",
    ),
    reindex: bool = typer.Option(
        False,
        "--reindex",
        help="Reindexar los TITN modificados (requiere --apply)",
    ),
) -> None:
    """Recalcula los titulos existentes desde el MARC guardado."""
    configure_logging()
    indexed = 0
    with session_scope() as session:
        stats = backfill_titles(
            session,
            apply=apply,
            limit=limit,
            fuente=fuente,
            material_only=material_only,
        )
        if apply and reindex and stats.changed_record_ids:
            indexed = MeiliIndexer().index_titns(session, stats.changed_record_ids)

    table = Table(title="Normalizacion de titulos")
    table.add_column("Metrica")
    table.add_column("Valor", justify="right")
    mode = "aplicado" if apply else "dry-run"
    if material_only:
        mode += " (solo material)"
    if fuente:
        mode += f" · {fuente}"
    table.add_row("Modo", mode)
    table.add_row("Ediciones leidas", str(stats.scanned))
    table.add_row("Titulos cambiados", str(stats.changed))
    table.add_row("Sin cambios", str(stats.unchanged))
    if reindex:
        table.add_row(
            "TITN reindexados",
            str(indexed) if apply else "no (requiere --apply)",
        )
    console.print(table)

    if stats.samples:
        sample_table = Table(title="Ejemplos de cambios")
        sample_table.add_column("TITN")
        sample_table.add_column("Antes")
        sample_table.add_column("Despues")
        for change in stats.samples:
            sample_table.add_row(
                change.titn,
                change.old_titulo or "",
                change.new_titulo or "",
            )
        console.print(sample_table)

    if not apply:
        console.print(
            "[yellow]Dry-run: no se ha modificado la base de datos. "
            "Usa --apply para aplicar.[/yellow]"
        )
    elif reindex and not stats.changed_titns:
        console.print("[green]No hay TITN que reindexar.[/green]")


@app.command("index")
def index_command(
    reset: bool = typer.Option(False, "--reset", help="Vaciar el indice antes de cargar"),
    fuente: str | None = typer.Option(None, "--fuente", help="Codigo de fuente"),
) -> None:
    """Construye el indice de Meilisearch desde PostgreSQL."""
    configure_logging()
    with session_scope() as session:
        source = get_fuente(session, fuente) if fuente else None
        total = MeiliIndexer().index_editions(
            session, reset=reset, fuente_id=source.id if source else None
        )
    console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("stats")
def stats_command() -> None:
    """Muestra un resumen del catalogo local."""
    with session_scope() as session:
        ediciones = session.scalar(select(func.count(Edicion.id))) or 0
        ejemplares = session.scalar(select(func.count(Ejemplar.id))) or 0
        bibliotecas = session.scalar(select(func.count(Biblioteca.id))) or 0

        table = Table(title="Mediateca Madrid")
        table.add_column("Metrica")
        table.add_column("Valor", justify="right")
        table.add_row("Ediciones", str(ediciones))
        table.add_row("Ejemplares", str(ejemplares))
        table.add_row("Bibliotecas", str(bibliotecas))
        console.print(table)


@app.command("status")
def status_command(
    limit: int = typer.Option(20, "--limit", min=1, help="Trabajos a mostrar"),
) -> None:
    """Muestra los trabajos de ingesta y la cobertura del catalogo."""
    with session_scope() as session:
        jobs = list(
            session.scalars(
                select(HarvestJob).order_by(HarvestJob.created_at.desc()).limit(limit)
            )
        )
        cover = coverage(session)

    jobs_table = Table(title="Trabajos de ingesta")
    for column in ("ID", "Tipo", "Estado", "Intentos", "Cursor", "Inicio", "Heartbeat"):
        jobs_table.add_column(column)
    for job in jobs:
        cursor = f"{job.cursor_doc or '—'}/{job.cursor_titn or '—'}"
        started = job.started_at.strftime("%Y-%m-%d %H:%M") if job.started_at else "—"
        heartbeat = (
            job.heartbeat_at.strftime("%Y-%m-%d %H:%M") if job.heartbeat_at else "—"
        )
        jobs_table.add_row(
            str(job.id),
            job.job_type,
            job.status,
            f"{job.attempts}/{job.max_attempts}",
            cursor,
            started,
            heartbeat,
        )
    console.print(jobs_table)

    coverage_table = Table(title="Cobertura del catalogo")
    coverage_table.add_column("Metrica")
    coverage_table.add_column("Valor", justify="right")
    coverage_table.add_row("Ediciones", str(cover.ediciones))
    coverage_table.add_row("Descubiertas", str(cover.descubiertas))
    coverage_table.add_row("Enriquecidas", str(cover.enriquecidas))
    coverage_table.add_row("Pendientes", str(cover.pendientes))
    coverage_table.add_row("Fallidas", str(cover.fallidas))
    coverage_table.add_row("Trabajos pendientes", str(cover.trabajos_pendientes))
    coverage_table.add_row("Trabajos en ejecucion", str(cover.trabajos_en_ejecucion))
    coverage_table.add_row("Trabajos completados", str(cover.trabajos_completados))
    coverage_table.add_row("Trabajos fallidos", str(cover.trabajos_fallidos))
    console.print(coverage_table)


@app.command("ingest-status")
def ingest_status_command(
    limit: int = typer.Option(20, "--limit", min=1, help="Trabajos a mostrar"),
) -> None:
    """Muestra trabajos, cobertura, metricas y salud del worker."""
    with session_scope() as session:
        jobs = recent_jobs(session, limit)
        cover = coverage(session)
        metrics = ingest_metrics(session, cover)
        worker = worker_state(session)

    jobs_table = Table(title="Trabajos de ingesta")
    for column in ("ID", "Tipo", "Estado", "Cursor", "Intentos", "Inicio", "Fin"):
        jobs_table.add_column(column)
    for job in jobs:
        cursor = f"{job.cursor_doc or '—'}/{job.cursor_titn or '—'}"
        started = job.started_at.strftime("%Y-%m-%d %H:%M") if job.started_at else "—"
        finished = job.finished_at.strftime("%Y-%m-%d %H:%M") if job.finished_at else "—"
        jobs_table.add_row(
            str(job.id),
            job.job_type,
            job.status,
            cursor,
            f"{job.attempts}/{job.max_attempts}",
            started,
            finished,
        )
    console.print(jobs_table)

    summary = Table(title="Cobertura y metricas de ingesta")
    summary.add_column("Metrica")
    summary.add_column("Valor", justify="right")
    summary.add_row("Ediciones", str(cover.ediciones))
    summary.add_row("Descubiertas", str(cover.descubiertas))
    summary.add_row("Enriquecidas", str(cover.enriquecidas))
    summary.add_row("Pendientes", str(cover.pendientes))
    summary.add_row("Fallidas", str(metrics.failed))
    summary.add_row("Desaparecidas", str(cover.fallidas))
    summary.add_row(
        "Porcentaje enriquecido",
        f"{round(cover.enriquecidas * 100 / cover.ediciones) if cover.ediciones else 0}%",
    )
    summary.add_row("Procesadas", str(metrics.processed))
    summary.add_row("Errores", str(metrics.errors))
    summary.add_row("Captchas", str(metrics.captchas))
    summary.add_row("Captchas resueltos", str(metrics.captchas_solved))
    summary.add_row("Captchas fallidos", str(metrics.captchas_failed))
    summary.add_row("Renovaciones de sesion", str(metrics.session_renewals))
    summary.add_row(
        "Tiempo medio por ficha",
        f"{metrics.average_ms:.2f} ms" if metrics.average_ms is not None else "—",
    )
    summary.add_row("Worker", worker.status)
    summary.add_row(
        "Ultimo heartbeat",
        worker.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")
        if worker.last_heartbeat
        else "—",
    )
    console.print(summary)


@app.command("worker")
def worker_command(
    once: bool = typer.Option(False, "--once", help="Procesa un trabajo y termina"),
    poll: float = typer.Option(settings.worker_poll_seconds, "--poll", min=0.1),
    heartbeat: float = typer.Option(
        settings.worker_heartbeat_seconds, "--heartbeat", min=0.0
    ),
    concurrency: int | None = typer.Option(
        None,
        "--concurrency",
        min=1,
        max=MAX_WORKER_CONCURRENCY,
        help="Tareas paralelas; si se omite, usa la configuracion del dashboard",
    ),
) -> None:
    """Reclama y ejecuta trabajos de la cola de ingesta."""
    configure_logging()

    if once:
        with session_scope() as session:
            job, backoff = worker_tick(
                session,
                handlers=DEFAULT_HANDLERS,
                heartbeat_seconds=heartbeat,
                heartbeat_file=settings.worker_heartbeat_file,
            )
        if job is None:
            console.print("[yellow]No hay trabajos pendientes[/yellow]")
        else:
            console.print(
                f"[green]Trabajo {job.id} ({job.job_type}) {job.status}[/green]"
                f" backoff={backoff:.0f}s"
            )
        return

    if concurrency is None:
        with session_scope() as session:
            effective = effective_worker_concurrency(session)
        origin = "configuracion"
    else:
        effective = concurrency
        origin = "cli"
    effective = max(1, min(effective, MAX_WORKER_CONCURRENCY))

    factory = get_session_factory()
    console.print(
        f"[green]Worker iniciado[/green] concurrencia={effective} origen={origin}"
    )
    threads = [
        threading.Thread(
            target=run_worker,
            kwargs={
                "session_factory": factory,
                "handlers": DEFAULT_HANDLERS,
                "poll_seconds": poll,
                "heartbeat_seconds": heartbeat,
                "heartbeat_file": settings.worker_heartbeat_file,
            },
            daemon=True,
        )
        for _ in range(effective)
    ]
    for thread in threads:
        thread.start()
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        console.print("Worker detenido")


@app.command("parse-file")
def parse_file_command(path: Path = typer.Argument(..., exists=True)) -> None:
    """Parsea una ficha HTML local y muestra el JSON resultante."""
    parsed = parse_file(str(path), url=str(path))
    console.print_json(json.dumps(asdict(parsed), ensure_ascii=False, default=str))


@app.command("scheduler")
def scheduler_command(
    once: bool = typer.Option(False, "--once", help="Revisa y encola una vez"),
    poll: float = typer.Option(
        settings.scheduler_poll_seconds, "--poll", min=1.0
    ),
) -> None:
    """Encola los trabajos de descubrimiento y enriquecimiento programados."""
    configure_logging()
    factory = get_session_factory()

    if once:
        with session_scope() as session:
            jobs = enqueue_due_jobs(session)
            session.commit()
        if jobs:
            console.print(
                "[green]Trabajos encolados:[/green] "
                + ", ".join(f"{job.id}:{job.job_type}" for job in jobs)
            )
        else:
            console.print("[yellow]No hay trabajos programados pendientes[/yellow]")
        return

    console.print("[green]Scheduler iniciado[/green]")
    try:
        run_scheduler(factory, poll_seconds=poll)
    except KeyboardInterrupt:
        console.print("Scheduler detenido")


@app.command("dashboard")
def dashboard_command(
    host: str | None = typer.Option(
        None, "--host", help="Host de escucha (por defecto, configuracion)"
    ),
    port: int | None = typer.Option(
        None, "--port", min=1, help="Puerto de escucha (por defecto, configuracion)"
    ),
    reload: bool = typer.Option(False, "--reload", help="Recargar al cambiar el codigo"),
) -> None:
    """Sirve la vista web de solo lectura del estado de la ingesta."""
    import uvicorn

    configure_logging()
    uvicorn.run(
        "mediateca.dashboard.app:app",
        host=host or settings.dashboard_host,
        port=port or settings.dashboard_port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
