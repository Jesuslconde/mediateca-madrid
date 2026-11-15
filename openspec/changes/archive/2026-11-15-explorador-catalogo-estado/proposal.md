# Proposal

## Why

Los trabajos de enriquecimiento terminan en `completed` aunque sigan existiendo miles de ediciones sin ficha OPAC o sin datos TMDB. El dashboard actual solo ofrece agregados que confunden "nunca intentado", "falló tras reintentos" y "TMDB no encontró coincidencia", de modo que el operador no puede saber qué falta, por qué falta ni priorizar el trabajo. Además, los fallos por ficha no se persisten: tras terminar el job solo quedan en `harvest_jobs.stats.failed` y desaparecen de la vista por edición.

## What Changes

- Añadir una página `/catalogo` de solo lectura en el dashboard, con resumen por estado, filtros y tabla paginada de ediciones.
- Añadir "Catálogo" al menú lateral común, sin duplicar las páginas de Inicio, Tareas y Configuración.
- Persistir el resultado del enriquecimiento OPAC por edición: `enrich_status` (`pending`, `enriched`, `failed`), `enrich_attempts`, `enrich_last_attempt_at` y `enrich_last_error`.
- Persistir el resultado del enriquecimiento TMDB por edición: `tmdb_status` (`pending`, `matched`, `unmatched`, `error`, `skipped`), `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error`. `tmdb_enriched_at` se conserva como fecha de la última coincidencia.
- Actualizar el harvester para escribir esas marcas en cada intento, éxito y fallo, sin cambiar la selección de pendientes ni la política de reintentos.
- Añadir una migración SQL idempotente y subir `SCHEMA_VERSION` a `4`.
- **BREAKING**: cualquier herramienta que asuma `SCHEMA_VERSION` `3` o que las columnas nuevas no existen debe actualizarse.

Fuera de alcance: cambios en la API pública del portal, escritura o encolado desde la página de catálogo, exportación CSV, cambios en la política de drenado del backlog y reintentos específicos por ficha.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `dashboard-ingesta`: nueva página de catálogo de solo lectura con resumen por estado, filtros, paginación y entrada en el menú lateral.
- `estado-ingesta`: el estado de enriquecimiento OPAC por edición deja de ser solo una fecha y pasa a incluir estado, intentos y último error persistidos.
- `enriquecimiento-tmdb`: el resultado TMDB por edición se persiste con estado explícito, incluido `unmatched`, para dejar de reintentar indistinguiblemente las ediciones sin coincidencia.
- `modelo-catalogo`: nuevas columnas de estado de enriquecimiento en `ediciones` y versión de esquema `4`.

## Impact

- `packages/shared/src/mediateca_shared/models.py`: columnas nuevas en `Edicion`.
- `packages/shared/src/mediateca_shared/version.py`: `SCHEMA_VERSION` a `4`.
- `services/enrich/scripts/`: nueva migración idempotente.
- `services/enrich/src/mediateca/catalog/harvester.py`: escritura de estado OPAC y TMDB por edición.
- `services/enrich/src/mediateca/catalog/repository.py`: helpers de estado y consultas filtrables.
- `services/enrich/src/mediateca/dashboard/`: ruta `/catalogo`, consultas, contexto y plantilla.
- `services/enrich/src/mediateca/dashboard/templates/base.html`: menú lateral.
- `services/enrich/tests/` y `packages/shared/tests/`: cobertura de migración, modelo, harvester y página.
- `docs/ARCHITECTURE_ENRICH.md` y `services/enrich/README.md`: documentación del nuevo estado y de la página.
