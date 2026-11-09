from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select

from mediateca.catalog.harvester import Harvester, OpacClient
from mediateca.catalog.indexer import MeiliIndexer
from mediateca.catalog.models import Biblioteca, Edicion, Ejemplar
from mediateca.catalog.parser import parse_file
from mediateca.core.config import settings
from mediateca.core.db import init_db, session_scope
from mediateca.core.logging import configure_logging, get_logger

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


@app.command("harvest")
def harvest_command(
    query: str = typer.Option("cine", "--query", "-q", help="Termino de busqueda"),
    max_pages: int = typer.Option(1, "--max-pages", min=1, help="Paginas maximas"),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Fichas maximas"),
    delay: float = typer.Option(1.0, "--delay", min=0.1, help="Segundos entre peticiones"),
    index: bool = typer.Option(False, "--index", help="Indexar al terminar"),
) -> None:
    """Recolecta fichas del OPAC y las guarda en PostgreSQL."""
    configure_logging()
    init_db()
    with session_scope() as session, OpacClient(delay=delay) as client:
        harvester = Harvester(session, client=client)
        stats = harvester.harvest_query(
            query, max_pages=max_pages, limit=limit, delay=delay
        )
    console.print(f"[green]Recoleccion terminada:[/green] {stats}")
    if index:
        with session_scope() as session:
            total = MeiliIndexer().index_editions(session, reset=False)
        console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("index")
def index_command(
    reset: bool = typer.Option(False, "--reset", help="Vaciar el indice antes de cargar"),
) -> None:
    """Construye el indice de Meilisearch desde PostgreSQL."""
    configure_logging()
    init_db()
    with session_scope() as session:
        total = MeiliIndexer().index_editions(session, reset=reset)
    console.print(f"[green]{total} ediciones indexadas[/green]")


@app.command("stats")
def stats_command() -> None:
    """Muestra un resumen del catalogo local."""
    init_db()
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


@app.command("parse-file")
def parse_file_command(path: Path = typer.Argument(..., exists=True)) -> None:
    """Parsea una ficha HTML local y muestra el JSON resultante."""
    parsed = parse_file(str(path), url=str(path))
    console.print_json(json.dumps(asdict(parsed), ensure_ascii=False, default=str))


def _run_harvest_job() -> None:
    logger.info("Iniciando recoleccion programada")
    try:
        for query in settings.queries:
            with session_scope() as session, OpacClient() as client:
                harvester = Harvester(session, client=client)
                stats = harvester.harvest_query(query, max_pages=2)
                logger.info("Recoleccion %s: %s", query, stats)
        with session_scope() as session:
            total = MeiliIndexer().index_editions(session)
        logger.info("Indexadas %s ediciones", total)
    except Exception:  # noqa: BLE001
        logger.exception("Fallo la recoleccion programada")


@app.command("scheduler")
def scheduler_command() -> None:
    """Ejecuta la recoleccion de fichas periodicamente."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    configure_logging()
    init_db()
    try:
        MeiliIndexer().ensure_index()
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo preparar Meilisearch")

    scheduler = BlockingScheduler(timezone="Europe/Madrid")
    now = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(
        _run_harvest_job,
        "interval",
        hours=settings.scheduler_harvest_hours,
        next_run_time=now,
        id="harvest",
    )
    console.print("[green]Scheduler iniciado[/green]")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("Scheduler detenido")


if __name__ == "__main__":
    app()
