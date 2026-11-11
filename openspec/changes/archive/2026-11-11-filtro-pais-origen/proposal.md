# Proposal

## Why

La ingesta ya puede obtener de TMDB los países de origen y publicarlos en el índice, pero la API y el portal todavía no los exponen ni permiten acotar la búsqueda por país. Sin este cambio, el dato enriquecido no aporta ninguna utilidad al usuario final.

## What Changes

- Añadir el parámetro `paises_origen` a `GET /api/search`, combinable con la consulta y el resto de filtros, y devolver la distribución de la faceta `paises_origen`.
- Exponer `paises_origen` en los resultados de búsqueda y en la ficha de registro de la API.
- Añadir al portal un filtro lateral por país de origen, mostrar los países en las tarjetas y en la ficha, y traducir los códigos ISO a etiquetas en español.
- Actualizar el wheel compartido a `0.2.0` y regenerar `openapi.json` y los tipos del frontend para incorporar el nuevo campo.
- Mostrar la atribución de TMDB que exigen sus condiciones de uso.
- **BREAKING**: la API requiere el esquema `2` y un índice reindexado con `paises_origen`; con el wheel anterior o un índice sin reindexar el campo no aparecerá.
- Este cambio depende del cambio `pais-origen-tmdb` de `mediateca-madrid-enrich`, que crea el dato y lo publica en Meilisearch.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `busqueda-facetas`: se añade `paises_origen` como faceta y como filtro combinable en la búsqueda de la API.
- `api-portal`: se añade el parámetro `paises_origen` y el campo `paises_origen` en los resultados y en la ficha de registro.
- `portal-web`: se añade el filtro por país de origen, la visualización de los países y la atribución de TMDB.

## Impact

- `backend/src/mediateca/catalog/search.py`: `FACET_FIELDS`, `build_filters` y `search` con `paises_origen`.
- `backend/src/mediateca/api/routers/search.py`: parámetro `paises_origen` repetible.
- `backend/src/mediateca/api/serializers.py`: `paises_origen` en la ficha de registro.
- `backend/src/mediateca/api/schemas.py`: reexporta los esquemas actualizados del wheel compartido.
- `backend/vendor/` y `backend/pyproject.toml`: wheel `mediateca-shared==0.2.0`.
- `frontend/components/FacetFilters.tsx`, `RecordCard.tsx` y `app/buscar/page.tsx`: filtro, chip activo y visualización.
- `frontend/app/registro/[titn]/page.tsx` y `frontend/lib/labels.ts`: países de la ficha y etiquetas ISO.
- `frontend/contracts/openapi.json` y `frontend/lib/api-types.ts`: regeneración del contrato.
- `backend/tests/` y pruebas del frontend o comprobaciones de `next build`: filtro, serialización y tipos.
- `README.md` y documentación del proyecto: uso del filtro, dependencia del cambio de ingesta y atribución de TMDB.
- Dependencia externa: índice de Meilisearch con `paises_origen` filtrable y facetado.
