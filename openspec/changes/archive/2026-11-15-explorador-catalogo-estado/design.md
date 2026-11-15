# Design

## Context

Ver `proposal.md - Why`. El dashboard es una app FastAPI con plantillas Jinja en `services/enrich/src/mediateca/dashboard/`; comparte sesión SQLAlchemy con el worker y solo escribe configuración y trabajos. `Edicion` (`packages/shared/src/mediateca_shared/models.py`) ya guarda `detail_fetched_at`, `tmdb_enriched_at`, `missing_at` e `is_stub`, pero no conserva el resultado del último intento por ficha. Las migraciones son SQL idempotente en `services/enrich/scripts/` y se aplican en orden alfabético; `SCHEMA_VERSION` está en `3`.

Restricciones:

- La selección de pendientes y la política de reintentos no cambian en este cambio; eso corresponde a `drenar-backlog-enriquecimiento`.
- La página es de solo lectura y no debe ejecutar escrituras.
- El modelo compartido se instala en API e ingesta; cualquier columna nueva exige migración y reconstrucción de ambas imágenes.

## Goals / Non-Goals

**Goals:**

- Exponer una vista global y filtrable del estado de enriquecimiento por edición.
- Distinguir de forma persistente "nunca intentado", "falló" y "TMDB sin coincidencia".
- Mantener la página como lectura pura, reutilizando la sesión y el menú del dashboard.
- Cambiar el modelo de forma compatible con datos existentes.

**Non-Goals:**

- Cambiar qué ediciones selecciona el enriquecimiento o cuántas reintenta.
- Añadir escritura, encolado o exportación desde la página.
- Guardar historial completo de intentos (solo el último resultado y un contador).
- Tocar la API pública del portal.

## Decisions

### Columnas en `ediciones`, no tabla auxiliar

Se añaden las columnas directamente en `ediciones`:

```text
enrich_status         VARCHAR(16)  NOT NULL DEFAULT 'pending'
enrich_attempts       INTEGER      NOT NULL DEFAULT 0
enrich_last_attempt_at TIMESTAMPTZ
enrich_last_error     TEXT
tmdb_status            VARCHAR(16) NOT NULL DEFAULT 'pending'
tmdb_attempts          INTEGER      NOT NULL DEFAULT 0
tmdb_last_attempt_at   TIMESTAMPTZ
tmdb_last_error        TEXT
```

Alternativa descartada: una tabla `edicion_enriquecimiento` con historial. Añade joins y escrituras por intento sin que el producto pida historial; basta el último resultado y un contador.

Los valores de estado se validan en aplicación (constantes en `mediateca_shared`), no con `CHECK`, para que una migración idempotente no tenga que recrear restricciones.

Índices nuevos: `ix_ediciones_enrich_status`, `ix_ediciones_tmdb_status` y sendos compuestos con `titn` para filtro + orden estable.

### `tmdb_enriched_at` sigue significando "última coincidencia"

No se reutiliza como marca de intento. `unmatched`, `error` y `skipped` actualizan `tmdb_status`, `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error`, pero no `tmdb_enriched_at`. Así el backfill existente sigue usando su criterio actual y la vista puede separar "sin intentar" de "intentado sin coincidencia".

### Escritura del estado en el harvester

Se centraliza en helpers de `catalog/repository.py`:

- `record_enrich_success(session, edicion)` → `enriched`, limpia error, incrementa intentos, fecha.
- `record_enrich_failure(session, titn, error)` → `failed`, incrementa intentos, guarda error.
- `record_tmdb_outcome(session, edicion, status, error=None)` → actualiza estado e intentos.

Punto crítico: `_enrich_titn` y `_enrich_tmdb` hacen `rollback()` al fallar. La marca de fallo MUST escribirse **después** del rollback, en una transacción nueva, o se perdería con la ficha fallida. Por eso el estado de fallo se registra en el bloque `except` de `harvest_enrichment`/`_enrich_tmdb`, no dentro de la transacción que se revierte.

`enrich_attempts` cuenta pases terminados (éxito o fallo terminal); `tmdb_attempts` cuenta consultas terminadas (matched, unmatched o error). `skipped` por falta de token no incrementa intentos. Alternativa descartada: contar cada reintento HTTP interno; mezclaría reintentos de red con intentos de enriquecimiento y haría ruido en la vista.

### Página y consultas

Nueva ruta `GET /catalogo` en `dashboard/app.py` con `_catalogo_context`, una plantilla `catalogo.html` y un módulo de consultas `dashboard/catalog_queries.py` para no engordar `queries.py`.

- Resumen: `GROUP BY enrich_status` y `GROUP BY tmdb_status` sobre el mismo filtro, más `COUNT` total y `COUNT` de `missing_at IS NOT NULL`.
- Filtros: estado OPAC, estado TMDB, desaparición (`incluir|excluir|solo`), texto (`TITN` o título con `ILIKE`), `soporte_principal`, biblioteca (`EXISTS` sobre `ejemplares`), rango de año, idioma y `pais`.
- Paginación: `page` y `limit` con tope (por ejemplo 200), `ORDER BY titn`, total de coincidencias para los controles.
- Los filtros se construyen como query string GET; la página no tiene formularios POST.
- El contexto reutiliza `_base_context` con `section="catalogo"` y `refresh_seconds=None` para no recargar mientras se filtra.

Alternativa descartada: reutilizar la API pública `/api/search` de Meilisearch. El índice solo contiene fichas completas (`detail_complete=true`) y no expone los estados internos de enriquecimiento, que son el objetivo de la página.

### Rendimiento y portabilidad

`ILIKE '%texto%'` sobre 67k filas es aceptable para uso interno; si el coste crece, se añadirá `pg_trgm` en otro cambio. La paginación por `OFFSET` es suficiente para el volumen actual. Las consultas usan solo SQLAlchemy portable para que los tests con SQLite puedan cubrirlas; la migración SQL, con `json`/`timestamptz`, se valida contra PostgreSQL en el stack.

### Migración y compatibilidad

Nueva migración `migrate_enriquecimiento_estado.sql`:

1. `ADD COLUMN IF NOT EXISTS` con defaults.
2. Backfill: `enrich_status='enriched'` donde `detail_fetched_at IS NOT NULL`; `tmdb_status='matched'` donde `tmdb_enriched_at IS NOT NULL`.
3. Índices `IF NOT EXISTS`.
4. `schema_meta.schema_version = '4'`.
5. `SCHEMA_VERSION = "4"` en `packages/shared`.

El orden `db -> init -> batch/web` ya aplica migraciones antes de arrancar API y worker, así que no hay ventana con columnas ausentes.

## Risks / Trade-offs

- [El fallo se marca después del rollback y una caída entre ambos deja la edición como `pending`] → Es el mismo estado que hoy; el siguiente lote la reintenta.
- [`enrich_attempts` no distingue reintentos de red de pases] → Se documenta como "pases de enriquecimiento", suficiente para priorizar.
- [Texto con `ILIKE` puede ser lento] → Aceptable a 67k; se deja `pg_trgm` como mejora futura.
- [La migración no se ejecuta en tests SQLite] → Se prueba el modelo y las consultas en SQLite y la migración en PostgreSQL vía `make migrate`/integración.
- [Cambio de `SCHEMA_VERSION` obliga a reconstruir ambas imágenes] → Ya es el flujo documentado en el README.

## Migration Plan

1. Aplicar la migración con `make migrate` (o el servicio `init`).
2. Reconstruir y desplegar `mediateca-batch` y `mediateca-web`.
3. Rollback: las columnas nuevas son aditivas; revertir imágenes y dejar las columnas sin uso. No se eliminan datos.
