# Tasks

## 1. Modelo y migración

- [ ] 1.1 Añadir `obra_manual`, `obra_manual_at` a `Edicion` y `manual`, `updated_at` a `Obra` en `packages/shared/src/mediateca_shared/models.py`; verificar con `pytest packages/shared/tests/test_schema.py`.
- [ ] 1.2 Crear `services/enrich/scripts/migrate_agrupacion_manual.sql` con las columnas y `schema_version = 8`, y subir `SCHEMA_VERSION` a `8`; verificar que `make test-migrations` ejecuta las migraciones dos veces sin error.
- [ ] 1.3 Actualizar las aserciones de versión y columnas en `packages/shared/tests/test_schema.py` y `services/enrich/tests/test_migrations.py`; verificar que ambas pruebas pasan.

## 2. Dominio de agrupación

- [ ] 2.1 Implementar `services/enrich/src/mediateca/catalog/grouping.py` con agrupar en obra existente, crear obra y agrupar, desvincular y limpieza de obras vacías; verificar con tests unitarios que las ediciones se mueven y que ninguna obra con ediciones se elimina.
- [ ] 2.2 Modificar `upsert_edicion()` para respetar `obra_manual` y marcar como manuales las ediciones que caen en una obra manual; verificar con un test de reingesta que la obra se conserva.
- [ ] 2.3 Verificar la unicidad de `(titulo_uniforme, anio)` al crear una obra manual reutilizando la existente; añadir test de que no se duplica la obra.
- [ ] 2.4 Añadir tests de desvinculación que comprueben el recálculo automático y la actualización de `Obra.manual`; verificar con `pytest services/enrich/tests/test_repository.py`.

## 3. Dashboard de agrupación

- [ ] 3.1 Añadir consultas de listado, filtros, resumen y obras candidatas para `/agrupacion` en `services/enrich/src/mediateca/dashboard/`; verificar con tests de consultas sobre SQLite.
- [ ] 3.2 Crear `templates/agrupacion.html`, registrar la ruta GET y añadir el enlace al menú de `base.html`; verificar con un test de `TestClient` que la página carga y muestra ediciones.
- [ ] 3.3 Implementar los POST de agrupar en obra existente, agrupar en obra nueva y volver a automático con `_has_write_access()` y reindexado de las ediciones afectadas; verificar con tests de éxito, error de token y selección inválida.
- [ ] 3.4 Documentar la página y el flujo manual en `docs/ARCHITECTURE_ENRICH.md`; verificar que el documento describe `/agrupacion` y el reindexado posterior.

## 4. Índice y búsqueda agrupada

- [ ] 4.1 Añadir `obra_id`, `obra_key` y `obra_titulo` a `build_document()` y a `FILTERABLE_ATTRIBUTES` en `services/enrich/src/mediateca/catalog/indexer.py`; verificar con tests del indexador que una edición sin obra usa `edicion:<record_id>`.
- [ ] 4.2 Usar `distinct: "obra_key"` en la consulta de hits de `CatalogSearch.search()` y hacer una segunda consulta sin `distinct` para facetas y `total_ediciones`; verificar con un índice falso que se envían ambos parámetros y que los totales se distinguen.
- [ ] 4.3 Comprobar en Meilisearch `v1.12` que `distinct` mantiene paginación y totales correctos con varias ediciones por obra; si el total no es fiable, ajustar el cálculo antes de continuar.
- [ ] 4.4 Añadir tests de reindexado tras agrupar y desvincular; verificar que solo se actualizan los documentos de las ediciones afectadas.

## 5. API y contrato

- [ ] 5.1 Ampliar `SearchHit` y `SearchResponse` en `packages/shared/src/mediateca_shared/schemas.py` con `obra_id`, `obra_titulo`, `ediciones_count` y `total_ediciones`; verificar con tests de esquema.
- [ ] 5.2 Implementar la agregación de hits por obra en `services/api` consultando las ediciones de la obra y uniendo soportes, bibliotecas y ejemplares; verificar con tests de búsqueda que una obra con cuatro ediciones devuelve un solo hit agregado.
- [ ] 5.3 Añadir `ObraOut.ediciones` y serializar las ediciones hermanas en `GET /api/records/{record_id}`; verificar con tests de que la ficha incluye `record_id`, fuente, soportes y `source_url` de cada edición.
- [ ] 5.4 Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts` con `make contracts`; verificar que la compilación web acepta los nuevos campos.

## 6. Portal

- [ ] 6.1 Adaptar `RecordCard` y la cabecera de `/buscar` para mostrar una tarjeta por obra, la unión de soportes, `ediciones_count` y el texto `X obras · Y ediciones`; verificar con `cd apps/web && npm run build`.
- [ ] 6.2 Añadir la sección de ediciones de la misma obra en `apps/web/app/registro/[recordId]/page.tsx`; verificar que una edición con hermanas las lista y que una edición única no muestra la sección.
- [ ] 6.3 Revisar que los favoritos y los enlaces usan la edición representativa sin romper `record_id`; verificar manualmente una búsqueda agrupada y el enlace a la ficha.

## 7. Integración y despliegue

- [ ] 7.1 Ejecutar `make test`, `make lint` y `make contracts`; verificar que todas las suites pasan y que no hay deriva entre contrato y tipos.
- [ ] 7.2 Aplicar `make init` sobre una base de pruebas con datos y verificar que la migración deja `SCHEMA_VERSION=8` y reconstruye el índice con `obra_key`.
- [ ] 7.3 Probar el caso real de *La vida padre*: agrupar sus cuatro ediciones desde `/agrupacion`, comprobar una sola tarjeta en `/buscar`, abrir la ficha y verificar las ediciones hermanas.
- [ ] 7.4 Reingerir una de las ediciones manuales y verificar que conserva su obra; ejecutar “Volver a automático” y comprobar que se recalcula.
- [ ] 7.5 Actualizar `README.md` o `docs/ARCHITECTURE.md` con el flujo de agrupación y el requisito de reindexado; verificar que las instrucciones coinciden con los comandos del Makefile.

## Workflow follow-up

- Archivar el cambio después de que la revisión del proyecto esté satisfecha.
- Verificar el resultado archivado y que las specs principales reflejan la agrupación manual.
