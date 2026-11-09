# Tasks

## 1. Modelo y persistencia

- [x] 1.1 En `backend/src/mediateca/catalog/models.py`, eliminar `Edicion.disponible`, `Ejemplar.disponible`, `Ejemplar.estado`, la relación `Ejemplar.historial` y la clase `HistorialDisponibilidad`; verificar con un test que `Base.metadata.tables` no contiene esas columnas ni la tabla `historial_disponibilidad`.
- [x] 1.2 En `backend/src/mediateca/catalog/repository.py`, quitar `_register_history` y las asignaciones de `estado`/`disponible` en `_sync_ejemplares`, y eliminar `edicion.disponible` de `upsert_edicion`; ejecutar `pytest backend/tests/test_repository.py` y comprobar que la tenencia por biblioteca sigue guardándose.
- [x] 1.3 En `backend/src/mediateca/catalog/parser.py`, quitar `estado` y `disponible` de `ParsedEjemplar`, la propiedad `ParsedEdicion.disponible` y la lectura de `data-disp`/columna de disponibilidad en `_parse_ejemplares`; verificar que `parse_file` de los dos fixtures no falla y conserva biblioteca, sucursal, signatura, tipo y soporte.
- [x] 1.4 Actualizar `backend/tests/test_parser.py` y `backend/tests/test_repository.py`: eliminar aserciones de `disponible`/`estado` y el test de historial, ajustar el conteo de ejemplares y añadir una aserción de que la edición expone sus bibliotecas tenedoras; verificar con `pytest -q backend/tests`.

## 2. Índice y búsqueda

- [x] 2.1 En `backend/src/mediateca/catalog/indexer.py`, quitar `disponible` de `FACET_FIELDS`, `FILTERABLE_ATTRIBUTES`, `build_document`, `build_filters` y `MeiliIndexer.search`, manteniendo `bibliotecas` y el conteo `ejemplares`; verificar que `build_document` no contiene la clave `disponible`.
- [x] 2.2 Añadir `backend/tests/test_indexer.py` que construya una edición en memoria y compruebe que el documento incluye `bibliotecas` y no incluye `disponible` ni campos de préstamo; verificar con `pytest backend/tests/test_indexer.py`.

## 3. API

- [x] 3.1 En `backend/src/mediateca/api/schemas.py`, quitar `disponible` de `EjemplarOut` y `RecordDetail`, y `disponibles` de `LibraryOut`; verificar que la app importa sin errores con `python -c "from mediateca.api.main import app"`.
- [x] 3.2 En `backend/src/mediateca/api/serializers.py`, eliminar `disponible`/`estado` de cada ejemplar y `disponible` de la edición, manteniendo `source_url` y los datos de biblioteca; verificar que `serialize_record` no devuelve claves de disponibilidad.
- [x] 3.3 En `backend/src/mediateca/api/routers/search.py`, retirar el parámetro `disponible` y devolver `400` si el cliente lo envía; en `backend/src/mediateca/api/routers/libraries.py`, quitar el cálculo y campo `disponibles`; verificar con `pytest` y una petición de humo a `/api/search?disponible=true` que responde `400`.
- [x] 3.4 Añadir `backend/tests/test_serializers.py` que compruebe ausencia de claves de disponibilidad y presencia de `source_url`; verificar con `pytest backend/tests/test_serializers.py`.

## 4. Portal web

- [x] 4.1 En `frontend/lib/api.ts`, quitar `disponible` de `SearchHit` y `Ejemplar`, y `disponibles` de `Library`; verificar que `npm run build` compila sin referencias sobrantes.
- [x] 4.2 Sustituir `frontend/components/AvailabilityTable.tsx` por una tabla de bibliotecas tenedoras que muestre biblioteca, sucursal, signatura, tipo y soporte, con un enlace a la ficha del OPAC recibida por prop; actualizar la importación en la página de ficha y verificar con `npm run build`.
- [x] 4.3 En `frontend/components/RecordCard.tsx`, quitar el estado «Disponible/No disponible» y mostrar solo el número de ejemplares y bibliotecas; verificar que no quedan referencias a `hit.disponible`.
- [x] 4.4 En `frontend/components/FacetFilters.tsx`, eliminar la casilla «Solo disponible» y el parámetro `disponible`; verificar que el formulario genera URLs sin ese parámetro.
- [x] 4.5 En `frontend/app/registro/[titn]/page.tsx`, quitar la insignia y el contador de disponibilidad y usar la nueva tabla con `record.source_url` como enlace al OPAC; verificar con `npm run build`.

## 5. Operación, migración y documentación

- [x] 5.1 En `backend/src/mediateca/cli.py`, eliminar el comando `refresh-availability` y `_run_availability_job`, y quitar el job `availability` del `scheduler`; verificar que `mediateca --help` no lista `refresh-availability`.
- [x] 5.2 En `backend/src/mediateca/core/config.py` eliminar `scheduler_availability_hours`, y quitarla de `.env.example` y `docker-compose.yml`; verificar con `grep -R scheduler_availability` que no quedan referencias.
- [x] 5.3 Añadir `scripts/migrate_disponibilidad.sql` con `DROP TABLE IF EXISTS historial_disponibilidad` y `ALTER TABLE ... DROP COLUMN IF EXISTS` para las columnas de disponibilidad, y un objetivo `migrate-disponibilidad` en `Makefile` que lo ejecute con `psql`; verificar ejecutándolo dos veces seguidas sin error sobre una base de desarrollo.
- [x] 5.4 En `Makefile`, eliminar el objetivo `refresh` y su entrada en `.PHONY`; verificar con `make help` que ya no aparece.
- [x] 5.5 Actualizar `README.md`, `backend/README.md` y `docs/ARCHITECTURE.md`: quitar el refresco de disponibilidad, documentar el enlace al OPAC y el paso de migración; verificar con `grep -Rni "disponibilidad\|refresh-availability\|Solo disponible"` que solo quedan menciones acordes al nuevo comportamiento.

## 6. Integración

- [x] 6.1 Ejecutar `pytest -q` y `ruff check src tests` en `backend/` y corregir cualquier fallo.
- [x] 6.2 Ejecutar `npm run build` en `frontend/` y corregir cualquier error de tipos o referencias.
- [x] 6.3 Con la pila levantada, ejecutar `make demo`, reindexar con `docker compose exec api mediateca index --reset` y comprobar que `/api/records/{titn}` no devuelve campos de disponibilidad y sí `source_url`, y que `/api/search?disponible=true` responde `400`.

## Workflow follow-up

- Archivar el cambio cuando la implementación y la revisión estén completas.
- Verificar el resultado archivado en `openspec/specs/`.
