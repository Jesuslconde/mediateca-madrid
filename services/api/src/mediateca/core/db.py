from __future__ import annotations

from collections.abc import Generator

from mediateca_shared.models import SchemaMeta
from mediateca_shared.version import check_schema_version
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from mediateca.core.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _session_factory


def get_schema_version() -> str | None:
    with get_session_factory()() as session:
        return session.scalar(
            select(SchemaMeta.value).where(SchemaMeta.key == "schema_version")
        )


def check_schema() -> None:
    check_schema_version(get_schema_version())


def get_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
