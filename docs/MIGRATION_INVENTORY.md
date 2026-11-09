# Inventario de extracción de la ingesta

Etiqueta de referencia: `pre-enrich-extraction`.

## Movido a mediateca-madrid-shared

- `backend/src/mediateca/catalog/models.py` → `mediateca_shared.models`
- `backend/src/mediateca/catalog/soportes.py` → `mediateca_shared.soportes`
- `backend/src/mediateca/api/schemas.py` → `mediateca_shared.schemas`
- `backend/src/mediateca/core/db.py::Base` → `mediateca_shared.db.Base`
- Constantes de trabajos → `mediateca_shared.constants`
- `SCHEMA_VERSION` y comprobación → `mediateca_shared.version`
- Contrato `contracts/openapi.json`

## Movido a mediateca-madrid-enrich

- `catalog/harvester.py`
- `catalog/parser.py`
- `catalog/repository.py`
- `catalog/jobs.py`
- escritura de `catalog/indexer.py`
- `cli.py`, `__main__.py`
- `core/config.py`, `core/db.py`, `core/search.py` de ingesta
- `scripts/migrate_disponibilidad.sql`, `scripts/migrate_ingesta.sql`
- `fixtures/`
- `tests/test_parser.py`, `test_repository.py`, `test_jobs.py`, `test_indexer.py`
- servicios `worker` y `scheduler`, volúmenes de snapshots y variables de ingesta

## Permanece en mediateca-madrid

- `api/` (FastAPI, routers, serializers, schemas reexportados)
- `catalog/search.py` (búsqueda de solo lectura)
- `core/config.py`, `core/db.py`, `core/search.py`, `core/logging.py` de lectura
- `frontend/`
- `tests/test_api.py`
- `openspec/specs/api-portal`, `portal-web`, `busqueda-facetas`, `modelo-catalogo`, etc.
