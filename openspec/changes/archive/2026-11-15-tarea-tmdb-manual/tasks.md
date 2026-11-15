# Tasks

## 1. Tipo de trabajo y cola

- [x] 1.1 Añadir `tmdb` a `JOB_TYPES` en `packages/shared` y verificar que el paquete importa sin errores
- [x] 1.2 Añadir `enqueue_tmdb_job` y el handler `_tmdb_handler` en `catalog/jobs.py`, registrarlo en `DEFAULT_HANDLERS`, y verificar con tests que encola, ejecuta y falla con mensaje legible sin token

## 2. Selección y refresco

- [x] 2.1 Añadir `refresh` a `harvest_tmdb_enrichment` con selección de pendientes o de todas las ediciones ordenadas por `tmdb_enriched_at` y `TITN`, y verificar con el test de CLI de refresco
- [x] 2.2 Incluir el modo `refresh` en las estadísticas del lote y verificar que el handler lo propaga

## 3. Dashboard y CLI

- [x] 3.1 Añadir la rama `tmdb` en `POST /jobs` con lote, refresco y rechazo sin token, y verificar con tests del dashboard
- [x] 3.2 Añadir el formulario "Actualizar metadatos TMDB" en `tareas.html` con lote y casilla de refresco, y verificar que aparece y se deshabilita con un trabajo activo
- [x] 3.3 Añadir `--refresh` al comando `tmdb-enrich` y verificar con un test de CLI

## 4. Scheduler y garantías

- [x] 4.1 Verificar con un test que el scheduler nunca encola trabajos `tmdb`
- [x] 4.2 Comprobar que la deduplicación impide dos trabajos `tmdb` activos y que el resumen por tipo incluye `tmdb`

## 5. Documentación e integración

- [x] 5.1 Documentar en `services/enrich/README.md` y `docs/ARCHITECTURE_ENRICH.md` la tarea manual, el modo refresco y el flag `--refresh`
- [x] 5.2 Ejecutar `make test-enrich` y `make lint`, y corregir cualquier fallo

## Workflow follow-up

- Archivar el cambio cuando la revisión del proyecto esté satisfecha.
- Verificar las specs principales actualizadas tras el archivado.
