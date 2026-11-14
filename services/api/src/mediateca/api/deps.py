from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

from mediateca.catalog.search import CatalogSearch
from mediateca.core.db import get_session


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


@lru_cache(maxsize=1)
def get_indexer() -> CatalogSearch:
    return CatalogSearch()
