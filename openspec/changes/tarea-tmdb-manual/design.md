# Design

## Context

La cola persistente ya ejecuta `discover`, `enrich` e `index` mediante
`DEFAULT_HANDLERS`, y el dashboard encola trabajos con `POST /jobs`. El
enriquecimiento TMDB ya existe en `Harvester.harvest_tmdb_enrichment` y en el
comando `mediateca tmdb-enrich`, pero no pasa por el worker ni aparece en
`/tareas`. Ver `proposal.md - Why`.

## Goals / Non-Goals

**Goals:**

- Reutilizar el backfill TMDB existente como trabajo de cola `tmdb`.
- Ofrecer el lote y el modo refresco desde el dashboard y la CLI.
- Mantener el trabajo estrictamente manual.
- Indexar los TITN procesados como el resto de lotes.

**Non-Goals:**

- Cambiar el esquema de base de datos o la API pública.
- Programar actualizaciones TMDB desde el scheduler.
- Descargar imágenes o almacenar pósters localmente.
- Añadir reintentos específicos para fichas sin coincidencia.

## Decisions

- **Nuevo tipo `tmdb` en `JOB_TYPES`.** Se integra en la deduplicación, el
  historial, las métricas por tipo y el bloqueo de acciones activas sin lógica
  adicional. Alternativa descartada: reutilizar `enrich`, que mezclaría consultas
  al OPAC con TMDB y rompería el contrato "solo TMDB".

- **Handler dedicado en `jobs.py`.** `_tmdb_handler` construye el cliente con
  `build_tmdb_client`, falla con un error legible si no hay token, ejecuta
  `harvest_tmdb_enrichment` con el lote y el modo del trabajo y reutiliza
  `_index_titns_for_job`. Alternativa descartada: ejecutar el comando CLI desde el
  worker, que duplicaría proceso y configuración.

- **Modo refresco en `harvest_tmdb_enrichment`.** Se añade `refresh: bool`. Sin
  refresco se conserva la selección actual (pendientes y fichas con `tmdb_id`
  sin `tmdb_url`). Con refresco se seleccionan todas las ediciones con
  `detail_fetched_at` y se ordenan por `tmdb_enriched_at` ascendente con
  `nulls_last()` y luego por `TITN`, de modo que cada lote avanza hacia las
  sincronizaciones más antiguas sin repetir siempre las mismas fichas.
  Alternativa descartada: cursor por `TITN` para el refresco, que obligaría a
  resetearlo en cada pasada y añadiría estado al trabajo.

- **Validación de token en el dashboard.** Antes de encolar se comprueba
  `effective_tmdb_api_token`; sin token se devuelve un error y no se crea trabajo.
  El handler mantiene la comprobación defensiva para encolados por CLI u otras
  vías.

- **Scheduler sin cambios.** Al no incluir `tmdb` en `enqueue_due_jobs`, la tarea
  queda manual por construcción; se añade un test que lo fija.

## Risks / Trade-offs

- [Refresco sin cursor puede repetir fichas si se interrumpe un lote] → La
  actualización es idempotente y la ordenación por antigüedad hace que el
  siguiente lote avance igualmente.
- [Las ediciones sin coincidencia no se marcan y quedan al final del refresco] →
  Se priorizan las ya sincronizadas y las no coincidentes se reintentan en el
  modo pendiente o al final de una pasada de refresco.
- [Consumo de cuota de TMDB] → Lote configurable y retardo del cliente; el
  scheduler nunca lo lanza.
- [Fallo de Meilisearch al indexar tras el lote] → Se reutiliza
  `pending_index_titns` y el reintento del trabajo, igual que en `enrich`.
