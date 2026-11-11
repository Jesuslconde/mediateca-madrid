# Tasks

## 1. Dependencia compartida

- [ ] 1.1 Sustituir el wheel de `backend/vendor/` por `mediateca_shared-0.2.0-py3-none-any.whl`, actualizar `backend/pyproject.toml` a `mediateca-shared==0.2.0`, y verificar que la imagen del backend instala el wheel y que `pytest -q` arranca con la nueva versión

## 2. Búsqueda y API

- [ ] 2.1 Añadir `paises_origen` a `FACET_FIELDS`, a `build_filters` con semántica OR y a `CatalogSearch.search`, y verificar con tests de un país, varios países y combinación con `genero` y `detail_complete`
- [ ] 2.2 Añadir el parámetro repetible `paises_origen` al router `GET /api/search` y verificar con tests que se propaga al adaptador de búsqueda y que la respuesta es 200
- [ ] 2.3 Añadir `paises_origen` a `serialize_record` y verificar con un test que `GET /api/records/{titn}` devuelve la lista de códigos y que una edición sin países devuelve una lista vacía
- [ ] 2.4 Documentar el nuevo parámetro y el campo de la ficha en `README.md` y `docs/ARCHITECTURE.md`, y verificar que los ejemplos de `curl` funcionan con la API levantada

## 3. Contrato OpenAPI y tipos

- [ ] 3.1 Exportar el contrato con `make openapi`, sincronizar `frontend/contracts/openapi.json` desde el contrato compartido y ejecutar `npm run generate:api`, y verificar que los tipos generados incluyen `paises_origen` en `SearchHit` y `RecordDetail` y el parámetro en la operación de búsqueda

## 4. Portal

- [ ] 4.1 Añadir a `FacetFilters` un selector múltiple de país con las opciones de `facets.paises_origen`, las etiquetas de `countryLabel`, los valores seleccionados y una nota de ayuda, y verificar con `npm run build`
- [ ] 4.2 Propagar `paises_origen` desde `app/buscar/page.tsx` a `searchRecords` y a los filtros activos, y verificar con `npm run build` que el chip y la consulta conservan los países seleccionados
- [ ] 4.3 Mostrar los países de origen en `RecordCard` y en la ficha de registro con etiquetas en español, y verificar con `npm run build` que una edición sin países no rompe la vista
- [ ] 4.4 Ampliar `lib/labels.ts` con los códigos ISO 3166-1 alfa-2 habituales y un respaldo al código, y verificar con `npm run build` que las etiquetas se renderizan
- [ ] 4.5 Añadir la atribución de TMDB y su enlace en el pie de página de `app/layout.tsx`, y verificar con `npm run build` que aparece en las páginas de inicio, búsqueda y ficha
- [ ] 4.6 Documentar en `README.md` el filtro por país, la dependencia del backfill y la atribución de TMDB, y verificar que las instrucciones coinciden con la interfaz

## 5. Integración y verificación

- [ ] 5.1 Ejecutar `pytest -q` en el backend y corregir cualquier fallo
- [ ] 5.2 Ejecutar `ruff check src tests` en el backend y corregir cualquier aviso
- [ ] 5.3 Ejecutar `npm run build` en el frontend y corregir cualquier error de tipos o de compilación
- [ ] 5.4 Con la ingesta migrada y reindexada, verificar `GET /api/search?paises_origen=ES`, la distribución de la faceta, la ficha con países y el filtro del portal de extremo a extremo
- [ ] 5.5 Verificar que la API arranca con `schema_meta.schema_version = 2` y falla con un error legible si el esquema no coincide

## Workflow follow-up

- Entrega recibida de `pais-origen-tmdb`: wheel `mediateca-shared` `0.2.0` y índice reindexado con `paises_origen`; sustituir `backend/vendor/`, regenerar `openapi.json` y los tipos del frontend.
- Archivar el cambio cuando la revisión del proyecto esté satisfecha.
- Verificar el resultado archivado y las specs principales actualizadas.
- Desplegar después de `pais-origen-tmdb` y de la reindexación completa del índice.
