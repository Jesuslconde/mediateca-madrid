# Proposal

## Why

El enriquecimiento automático selecciona pendientes con `discovery_seen_at >= since`, donde `since` es el inicio del último descubrimiento completado. En cuanto un descubrimiento nuevo termina, la ventana avanza y los stubs de cohortes anteriores que no llegaron a procesarse quedan huérfanos. Cada job termina en `completed` tras un solo lote y el operador debe pulsar "Enriquecer pendientes" repetidamente para avanzar. El resultado es un backlog histórico que nunca se drena solo.

## What Changes

- El scheduler SHALL contar y encolar el enriquecimiento sobre todos los pendientes (`since=None`), no solo sobre la última cohorte descubierta.
- Tras completar un lote `enrich` con progreso y pendientes restantes, el worker SHALL encolar automáticamente el siguiente lote para drenar el backlog, respetando la deduplicación existente.
- El encadenamiento inmediato tras un descubrimiento se conserva para priorizar lo nuevo, pero el drenado posterior continúa con todo el backlog.
- Añadir guardas de drenado: no encadenar si el lote procesó cero fichas, si no quedan pendientes o si se alcanzó el tope configurable de encadenamientos.
- Registrar en las estadísticas del job `pending_after`, `drain_chain`, `drained` y `stop_reason` para que el avance sea observable.
- Añadir configuración de entorno para activar o desactivar el drenado y fijar el tope de encadenamientos, con valores por defecto seguros.

Fuera de alcance: cambios de esquema de base de datos, nuevas páginas o acciones en el dashboard, reintentos adicionales por ficha, exclusión automática de fallos persistentes y cambios en el enriquecimiento TMDB.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `cola-trabajos`: la programación periódica del enriquecimiento deja de limitarse a la cohorte del último descubrimiento y se añade el drenado encadenado del backlog con guardas y trazabilidad.

## Impact

- `services/enrich/src/mediateca/catalog/scheduler.py`: conteo y encolado sobre todos los pendientes.
- `services/enrich/src/mediateca/catalog/jobs.py`: cálculo de pendientes y encadenamiento tras completar un lote.
- `services/enrich/src/mediateca/core/config.py`: nuevas variables de configuración del drenado.
- `services/enrich/src/mediateca/cli.py`: sin cambios funcionales salvo los valores por defecto compartidos.
- `services/enrich/tests/`: pruebas del scheduler, del encadenamiento y de las guardas.
- `docs/ARCHITECTURE_ENRICH.md` y `services/enrich/README.md`: documentación del drenado y de la configuración.
