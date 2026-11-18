# Proposal

## Why

El catálogo y toda la cadena de ingesta asumen una única fuente OPAC: una URL, una sesión, un filtro de formato y un `TITN` global. Añadir la Red de Bibliotecas Públicas de Andalucía —y después otras redes— exige una dimensión de fuente transversal. Sin ella, los `TITN` de distintos catálogos colisionan (el `TITN 48` existe en Madrid y en Andalucía con títulos distintos) y los trabajos, el índice, la API y las listas no pueden distinguir de qué catálogo procede una edición.

Este cambio prepara esa dimensión con Madrid como única fuente activa. No ingiere Andalucía todavía: deja el sistema listo para que el cambio `ingesta-andalucia` añada la segunda fuente sin volver a tocar la identidad, el contrato ni la migración.

## What Changes

- Nuevo registro persistente de fuentes con código estable (`madrid`), nombre, perfil OPAC (URL base, ruta, patrón de sesión, filtro de formato, tipo de adaptador) y configuración operativa (habilitada, retardo, captcha).
- Nueva identidad global `record_id = "<fuente>:<titn>"`. **BREAKING** para consumidores internos que usaban `titn` como clave única.
- `Edicion`, `Biblioteca`, `Sucursal` y `Ejemplar` ganan `fuente_id`; las unicidades pasan a `(fuente_id, titn)`, `(fuente_id, codigo)` y `(fuente_id, external_key)`.
- `Obra` sigue siendo global: puede agrupar ediciones de varias fuentes por título uniforme y año. No se hace deduplicación ni fusión de ediciones en este cambio.
- `HarvestJob` gana `fuente_id`; los cursores, la deduplicación y las reglas de exclusión se evalúan por fuente. El scheduler recorre las fuentes habilitadas.
- El índice usa `record_id` como `id`, añade `fuente` como campo filtrable y facetable, y prefija los códigos de ubicación (`b:<fuente>:<codigo>`, `s:<fuente>:<codigo>`).
- La API expone `GET /api/records/{record_id}` y mantiene la compatibilidad con `GET /api/records/{titn}` resolviendo a Madrid. Añade el filtro `fuente`, devuelve la fuente en la ficha y calcula `source_url` con el perfil de cada fuente.
- El portal usa `record_id` en los enlaces internos y mantiene válidas las URLs antiguas `/registro/{titn}`. Con una sola fuente, la interfaz no muestra un selector de comunidad.
- Las listas guardan `record_id`; una migración convierte los `titn` existentes a `madrid:<titn>`. La API de listas acepta ambas formas.
- Migración idempotente: crea el registro de fuentes, siembra `madrid`, rellena `fuente_id`, sustituye unicidades y sube `SCHEMA_VERSION`. Reindexado completo obligatorio.
- El dashboard y los logs incorporan la fuente en cobertura, trabajos y métricas.

Fuera de alcance:

- Datos, perfil operativo y habilitación de Andalucía (cambio `ingesta-andalucia`).
- Deduplicación o ficha única por película entre fuentes.
- Directorio de bibliotecas andaluz, direcciones, códigos postales nacionales y orden por cercanía fuera de Madrid.
- Renombrar el producto o cambiar el branding.
- Otros adaptadores OPAC distintos de AbsysNet.

## Capabilities

### New Capabilities

- `fuentes-opac`: registro de fuentes, contrato de adaptador OPAC y resolución de la identidad global de una edición.

### Modified Capabilities

- `modelo-catalogo`: fuente en edición, biblioteca y sucursal; unicidad compuesta; `Obra` global.
- `ingesta-catalogo`: perfil de fuente para sesión, búsqueda y filtro de formato; Madrid se comporta igual.
- `cola-trabajos`: trabajos, cursores, deduplicación y exclusión por fuente.
- `estado-ingesta`: cobertura y marcas de progreso por fuente.
- `dashboard-ingesta`: fuente en cobertura, catálogo y tareas.
- `observabilidad-ingesta`: fuente en logs y métricas.
- `busqueda-facetas`: `id` global, campo `fuente`, facetas y ubicaciones con fuente.
- `api-portal`: `record_id`, filtro y ficha con fuente, `source_url` por fuente y compatibilidad.
- `contratos-compartidos`: contrato OpenAPI y `SCHEMA_VERSION`.
- `portal-web`: enlaces por `record_id`, compatibilidad de URLs y etiqueta de fuente.
- `listas-compartidas`: elementos por `record_id` y migración de listas existentes.
- `directorio-bibliotecas`: emparejamiento de bibliotecas y sucursales por fuente.
- `operacion-despliegue`: migración, reindexado y configuración de fuentes.

## Impact

- `packages/shared`: modelos SQLAlchemy, esquemas Pydantic, constantes, `SCHEMA_VERSION` y utilidades de identidad.
- `services/enrich`: configuración, cliente OPAC, parser, repositorio, trabajos, scheduler, indexador, directorio, CLI, dashboard y migraciones SQL.
- `services/api`: serializadores, routers de búsqueda, fichas, bibliotecas y listas, esquemas y contrato OpenAPI.
- `apps/web`: cliente API, tipos generados, rutas de ficha, enlaces internos, listas y etiquetas de fuente.
- `contracts/openapi.json` y `apps/web/lib/api-types.ts`.
- Base de datos: migración de identidad y unicidades, migración de listas, `SCHEMA_VERSION` y reindexado completo de Meilisearch.
- Operación: el primer despliegue de este cambio requiere `init`, migración y `index --reset`; las URLs antiguas de Madrid deben seguir funcionando.
