# Proposal

## Why

El backfill de TMDB solo puede ejecutarse desde la CLI del worker. El operador
necesita refrescar portadas, enlaces y países de origen desde el mismo dashboard
que ya lanza el resto de tareas, sin acceso al host ni a `docker compose run`. La
tarea debe ser estrictamente manual: nunca debe consumir cuota de TMDB por una
ejecución programada.

## What Changes

- Añadir el tipo de trabajo `tmdb` a la cola, ejecutado por el worker como el
  resto de trabajos y visible en el historial.
- Exponer la tarea en `Tareas` (`/tareas`) con un lote configurable y una casilla
  para reactualizar también las ediciones ya sincronizadas.
- Mantener el modo por defecto de solo pendientes (sin `tmdb_enriched_at` o con
  `tmdb_id` sin `tmdb_url`) y añadir un modo de refresco que reconsulta todas las
  ediciones enriquecidas, ordenadas por sincronización más antigua.
- Rechazar el encolado desde el dashboard si no hay token de TMDB configurado,
  con un mensaje comprensible.
- Añadir `--refresh` al comando existente `mediateca tmdb-enrich` para mantener la
  paridad entre CLI y dashboard.
- Garantizar que el scheduler nunca encola trabajos `tmdb`; solo se lanzan a mano.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `cola-trabajos`: el tipo `tmdb` pasa a formar parte de los trabajos encolables y
  se declara explícitamente como no programable por el scheduler.
- `dashboard-ingesta`: la página de Tareas incluye la actualización de metadatos
  TMDB con lote, modo refresco y rechazo sin token; el resumen por tipo incluye
  `tmdb`.
- `enriquecimiento-tmdb`: el backfill manual se ofrece también como trabajo de
  cola y admite un modo de refresco de ediciones ya sincronizadas.

## Impact

- `packages/shared/src/mediateca_shared/constants.py`: nuevo tipo en `JOB_TYPES`.
- `services/enrich/src/mediateca/catalog/jobs.py`: encolado y handler `tmdb`.
- `services/enrich/src/mediateca/catalog/harvester.py`: modo `refresh` en
  `harvest_tmdb_enrichment`.
- `services/enrich/src/mediateca/dashboard/app.py` y
  `templates/tareas.html`: formulario y validación de la tarea.
- `services/enrich/src/mediateca/cli.py`: flag `--refresh`.
- `services/enrich/tests/`: cobertura de encolado, handler, dashboard, scheduler y
  CLI.
- `services/enrich/README.md` y `docs/ARCHITECTURE_ENRICH.md`: documentación.

No hay cambios de esquema de base de datos ni de contrato OpenAPI.
