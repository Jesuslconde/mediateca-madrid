# Design

## Context

Ver `proposal.md - Why`. `enqueue_due_jobs` (`catalog/scheduler.py`) usa `last_completed_discover(...).started_at` como `since` y `count_pending_titns(session, since=since)`; `_enqueue_enrich_after_discover` (`catalog/jobs.py`) encadena con `since=job.started_at`. `harvest_enrichment` respeta `job.stats.since` y `job.cursor_titn`, y `select_pending_titns(after_titn=...)` ya soporta continuar por `TITN`. `worker_tick` ejecuta el handler, llama a `finish_job` y hace commit; no hay encadenamiento tras un `enrich`.

El problema es doble: la ventana `since` deja fuera cohortes antiguas y cada job procesa un solo lote. No hace falta cambiar el modelo ni el dashboard para corregirlo.

## Goals / Non-Goals

**Goals:**

- Que el enriquecimiento automático cubra todo el backlog, no solo la última cohorte.
- Drenar el backlog con lotes encadenados y reanudables, sin bucles infinitos.
- Mantener la prioridad de lo recién descubierto.
- Dejar rastro del avance y del motivo de parada en las estadísticas del job.

**Non-Goals:**

- Cambiar el esquema de base de datos o `SCHEMA_VERSION`.
- Añadir UI nueva o acciones en el dashboard.
- Excluir automáticamente fichas con fallos persistentes; eso depende del estado por edición de `explorador-catalogo-estado`.
- Cambiar el comportamiento del enriquecimiento TMDB.

## Decisions

### Scheduler sobre todos los pendientes

En `enqueue_due_jobs`, el enriquecimiento deja de depender de `last_completed_discover`:

```python
pending = count_pending_titns(session)          # sin since
if pending > 0 and _is_due(last_job("enrich"), schedule.enrich_interval_hours, current):
    enqueue_enrich_job(session, since=None, batch_size=schedule.enrich_batch_size, reason="scheduler")
```

Se mantiene la deduplicación con `has_active_job("discover")`/`has_active_job("enrich")` y el intervalo. Alternativa descartada: mantener `since` y añadir otra ventana para "antiguos"; complica la consulta y deja dos políticas que se pisan.

### Drenado encadenado con cursor

Tras completar un `enrich`, `worker_tick` calcula el siguiente paso antes de cerrar el job:

```text
last_titn            = stats["cursor_titn"]          # último TITN recorrido, haya éxito o no
pending_total        = count_pending_titns(session)
pending_after_cursor = count_pending_titns(session, after_titn=last_titn)
progress             = stats["processed"] > 0
chain                = stats.get("drain_chain", 0)

si drained desactivado           -> stop_reason=disabled
si pending_total == 0            -> stop_reason=no_pending
si chain >= max_chain            -> stop_reason=max_chain
si pending_after_cursor > 0      -> encolar enrich(cursor_titn=last_titn, since=None)
si pending_after_cursor == 0 and progress -> encolar enrich(cursor_titn=None, since=None)  # vuelta
si pending_after_cursor == 0 and not progress -> stop_reason=no_progress
```

El cursor es la clave: si hay una cabeza de fallos persistentes, el lote avanza igualmente porque `select_pending_titns` filtra `titn > cursor`. Cuando el cursor llega al final, la vuelta reintenta los fallos solo si el lote anterior hizo algún progreso; si no, se detiene en vez de girar en vacío. Alternativa descartada: reencolar siempre desde el principio; una cabeza de fallos mayor que el lote bloquearía el drenado indefinidamente.

`count_pending_titns` gana el parámetro `after_titn`, simétrico a `select_pending_titns`, para decidir la vuelta sin traer filas.

### Dónde encadenar

Se añade `maybe_chain_enrich(session, job, stats)` en `catalog/jobs.py`, llamado desde `worker_tick` después de `finish_job` y del commit que deja el job en `completed`. Así `has_active_job("enrich")` ya no ve el job actual y la deduplicación funciona. Un fallo al encolar se captura y se registra; nunca convierte en fallido un lote que ya terminó bien.

Alternativa descartada: encadenar dentro de `_enrich_handler`. El job aún estaría `running`, la deduplicación lo rechazaría y habría que relajar `has_active_job`, con riesgo de duplicados.

### Configuración

Se añaden a `core/config.py`:

- `enrich_drain_enabled: bool = True` (`MEDIATECA_ENRICH_DRAIN_ENABLED`)
- `enrich_drain_max_chain: int = 100` (`MEDIATECA_ENRICH_DRAIN_MAX_CHAIN`)

Se leen de entorno, como el resto de parámetros del worker. No se exponen en el dashboard para no ampliar el formulario de programación en este cambio. Un valor de `0` o negativo en el tope se interpreta como "sin drenado" en la validación de configuración.

### Estadísticas

Cada lote `enrich` termina con:

- `pending_after`: pendientes totales tras el lote.
- `pending_after_cursor`: pendientes por delante del cursor.
- `drain_chain`: profundidad del encadenamiento (0 en el primer lote).
- `drained`: `true` si se encoló otro lote.
- `stop_reason`: `chain_forward`, `chain_wrap`, `no_pending`, `no_progress`, `max_chain`, `disabled` o `already_active`.

Así `/tareas`, la CLI y la futura página de catálogo pueden mostrar el avance sin consultar la base.

### Interacción con el encadenamiento tras descubrimiento

`_enqueue_enrich_after_discover` se conserva con `since=job.started_at` para priorizar lo nuevo. El primer lote drenado que le siga usará `since=None` y cubrirá el backlog histórico. No hay dos políticas en el scheduler: solo el encadenamiento inmediato tras un discover mantiene `since`, y es una optimización de orden, no una restricción permanente.

## Risks / Trade-offs

- [Fallos persistentes mantienen el backlog por encima de cero y el scheduler reencola cada intervalo] → Las guardas `no_progress`, `max_chain` y el cursor evitan bucles cerrados; el operador puede ver los fallos con `explorador-catalogo-estado` y desactivar el drenado.
- [Un lote con progreso mínimo (1 ficha) puede alargar la cadena] → `enrich_drain_max_chain` acota la profundidad y el scheduler reanuda en el siguiente intervalo.
- [Dos workers podrían intentar encadenar a la vez] → La deduplicación de `enqueue_job` rechaza el duplicado; el segundo recibe `JobAlreadyActive` y se registra como `already_active`.
- [Drenar todo el backlog consume cuota del OPAC y puede toparse con captchas] → Se respeta la pausa por captcha y el reintento existente; el drenado se detiene cuando el job no progresa.
- [El scheduler podría encolar enriquecimiento sin un descubrimiento previo] → Solo lo hace si `count_pending_titns` es mayor que cero, es decir, si ya hay stubs reales.

## Migration Plan

No hay migración de datos. Desplegar `mediateca-batch` con el worker y el scheduler nuevos. Rollback: `MEDIATECA_ENRICH_DRAIN_ENABLED=false` detiene el encadenamiento sin revertir datos; las estadísticas nuevas son aditivas.
