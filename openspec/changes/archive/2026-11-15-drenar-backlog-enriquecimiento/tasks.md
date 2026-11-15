# Tasks

## 1. Configuración y consulta de pendientes

- [x] 1.1 Añadir `enrich_drain_enabled` (por defecto `true`) y `enrich_drain_max_chain` (por defecto `100`) a `Settings`, documentarlos en `.env.example`, y verificar con tests que los valores por defecto y las variables `MEDIATECA_ENRICH_DRAIN_*` se leen correctamente
- [x] 1.2 Añadir el parámetro `after_titn` a `count_pending_titns` en `catalog/repository.py`, simétrico a `select_pending_titns`, y verificar con tests que cuenta todos los pendientes, los posteriores a un `TITN` y los de un `since` dado
- [x] 1.3 Normalizar en `Settings` o en la lógica de drenado un tope `<= 0` como drenado desactivado, y verificar con un test que no se encadena con tope cero

## 2. Scheduler sobre todos los pendientes

- [x] 2.1 Cambiar `enqueue_due_jobs` para contar `count_pending_titns(session)` sin `since` y encolar `enrich` con `since=None`, y verificar con un test que un stub de una cohorte anterior a la última descubierta provoca el encolado
- [x] 2.2 Verificar con tests que el scheduler no encola si no hay pendientes, si ya hay un `discover`/`enrich` activo o si el intervalo no se ha cumplido
- [x] 2.3 Verificar con un test que el encolado tras un descubrimiento conserva `since=started_at` y que el primer lote drenado posterior usa `since=None`

## 3. Drenado encadenado

- [x] 3.1 Añadir `cursor_titn` a `enqueue_enrich_job` y verificar con un test que el trabajo creado lo persiste y que `harvest_enrichment` continúa desde ahí
- [x] 3.2 Implementar `maybe_chain_enrich` en `catalog/jobs.py` con las decisiones `chain_forward`, `chain_wrap`, `no_pending`, `no_progress`, `max_chain`, `disabled` y `already_active`, y verificar con tests unitarios cada rama
- [x] 3.3 Llamar a `maybe_chain_enrich` desde `worker_tick` después de `finish_job` y del commit, y verificar con un test que un `enrich` completado con pendientes deja otro `enrich` `pending` con `drain_chain` incrementado
- [x] 3.4 Verificar con un test que un lote con `processed=0` no encadena y registra `stop_reason='no_progress'`, y que un lote con progreso que llega al final del cursor encadena con `cursor_titn=None` (`chain_wrap`)
- [x] 3.5 Verificar con un test que `enrich_drain_enabled=false` procesa un solo lote y que `enrich_drain_max_chain` detiene la cadena al alcanzar el tope
- [x] 3.6 Registrar en las estadísticas del job `pending_after`, `pending_after_cursor`, `drain_chain`, `drained` y `stop_reason`, y verificar con un test que quedan persistidos en `harvest_jobs.stats` y visibles en `/tareas`
- [x] 3.7 Verificar con un test que un fallo al encolar el siguiente lote no marca como fallido el lote ya completado y registra `already_active` o el error correspondiente

## 4. Documentación e integración

- [x] 4.1 Documentar en `docs/ARCHITECTURE_ENRICH.md` el scheduler sobre todos los pendientes, el drenado con cursor, las guardas, los motivos de parada y las variables `MEDIATECA_ENRICH_DRAIN_*`, verificando que los comandos descritos coinciden con `make`
- [x] 4.2 Documentar en `services/enrich/README.md` cómo se comporta el enriquecimiento automático y cómo desactivar el drenado
- [x] 4.3 Ejecutar `make test-enrich` y `make lint` y corregir cualquier fallo
- [x] 4.4 Verificación de integración: con una base con stubs antiguos y el scheduler en modo `--once`, comprobar que se encola un `enrich` sobre todos los pendientes y que tras dos lotes simulados el contador de pendientes desciende

## Workflow follow-up

- Archivar el cambio cuando la revisión del proyecto esté satisfecha.
- Verificar las specs principales actualizadas tras el archivado.
