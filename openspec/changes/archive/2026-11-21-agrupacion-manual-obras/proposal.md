# Proposal

## Why

La agrupación automática de obras usa el título uniforme y el año exactos, por lo que películas con ligeras variantes de catalogación aparecen como varios resultados distintos. En el caso de *La vida padre*, el portal muestra cuatro tarjetas de la misma película. La heurística automática no es fiable para todos los casos y el operador necesita una forma manual y persistente de corregir la agrupación sin que la siguiente ingesta la deshaga.

## What Changes

- Añadir a la edición las marcas `obra_manual` y `obra_manual_at`, y a la obra la marca `manual`.
- Hacer que la asignación manual de obra prevalezca siempre sobre la agrupación automática durante la reingesta y el enriquecimiento.
- Añadir una página `/agrupacion` al dashboard para seleccionar ediciones y agruparlas en una obra existente, buscada por texto, o en una obra nueva.
- Permitir desvincular una edición de su agrupación manual y devolverla al comportamiento automático.
- Mantener la unicidad de obra por título uniforme y año: si la obra destino ya existe, se reutiliza; no se crean obras manuales duplicadas.
- Añadir al índice de búsqueda la referencia a la obra (`obra_id`, `obra_key` y `obra_titulo`) y agrupar los resultados de búsqueda por obra.
- Devolver una sola tarjeta por obra en el portal, con la unión de soportes, bibliotecas y ejemplares, y mostrar en la ficha las demás ediciones de la misma obra.
- Ampliar el contrato de búsqueda y de ficha con la información de la obra y sus ediciones.
- Migración idempotente y `SCHEMA_VERSION` a `8`, con reconstrucción completa del índice.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `modelo-catalogo`: agrupación manual persistente de ediciones y marca de obra curada.
- `ingesta-catalogo`: la reingesta respeta la obra asignada manualmente y no la sobrescribe.
- `dashboard-ingesta`: nueva página de agrupación manual con selección de ediciones, obra destino y desvinculación.
- `busqueda-facetas`: documento de índice con referencia a la obra y búsqueda agrupada por obra.
- `api-portal`: resultados de búsqueda agrupados y ficha con las ediciones de la misma obra.
- `portal-web`: una tarjeta por obra y listado de ediciones hermanas en la ficha.
- `contratos-compartidos`: nuevos campos del contrato y `SCHEMA_VERSION` a `8`.
- `operacion-despliegue`: migración y reindexado completo para la agrupación manual.

## Impact

- `packages/shared`: modelos SQLAlchemy, esquemas Pydantic, `SCHEMA_VERSION` y contrato OpenAPI.
- `services/enrich`: repositorio, nueva lógica de agrupación, indexador, dashboard, plantillas y migración SQL.
- `services/api`: serializadores, esquema de búsqueda, agregación de obras y ficha de registro.
- `apps/web`: tipos generados, tarjeta de resultados, cabecera de resultados y ficha de registro.
- `contracts/openapi.json` y `apps/web/lib/api-types.ts`.
- Base de datos e índice de Meilisearch: migración, nuevas columnas y reindexado completo.
- Operación: despliegue coordinado de `mediateca-batch` y `mediateca-web`; el índice anterior debe reconstruirse para incluir `obra_key`.
