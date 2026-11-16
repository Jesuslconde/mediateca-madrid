# Proposal

## Why

El portal usa formularios GET nativos para buscar y filtrar, de modo que cada interacción recarga el documento completo y pierde la sensación de aplicación moderna. Además, el orden por año y por título ya existe en la API pero está enterrado en el panel de filtros y solo se aplica al pulsar «Aplicar filtros», y el enlace «Volver a la búsqueda» descarta la consulta y los filtros activos.

## What Changes

- Sustituir los formularios de búsqueda y filtros por navegación cliente de Next.js, sin recarga completa del documento.
- Mostrar el selector de orden en la cabecera de resultados y aplicarlo de inmediato, conservando la consulta y los filtros y volviendo a la página 1.
- Añadir estados de carga visibles (esqueletos y estado pendiente) al navegar a resultados y a la ficha.
- Desempatar los órdenes por año y por duración con el título ascendente, de forma estable.
- Volver de una ficha a la búsqueda conservando `q`, filtros, `sort` y `page`.

No hay cambios incompatibles: los valores de `sort` de la API y el contrato OpenAPI se mantienen.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `portal-web`: navegación cliente sin recarga completa, ordenación inmediata en la cabecera de resultados, estados de carga y vuelta a la búsqueda con el estado previo.
- `busqueda-facetas`: la ordenación por año y por duración desempata por título ascendente de forma estable.

## Impact

- `apps/web`: buscador, filtros, cabecera de resultados, paginación, ficha y enlaces de vuelta; nuevos componentes cliente y esqueletos de carga.
- `services/api`: mapa de órdenes de búsqueda y adaptador de Meilisearch; sin cambios en parámetros ni en el contrato OpenAPI.
- Pruebas de la API para el orden estable.
- Sin dependencias nuevas de frontend y sin reindexado: los campos ordenables ya existen en el índice.
- Fuera de alcance: cache cliente con TanStack Query o SWR, proxy BFF, SPA completa, normalización de artículos y acentos del título y un harness de tests de frontend.
