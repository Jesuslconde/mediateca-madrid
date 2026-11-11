# Arquitectura

## Repositorios

```text
mediateca-madrid-shared
  modelos SQLAlchemy + esquemas Pydantic + openapi.json + SCHEMA_VERSION
            │
            ├──────────────┬─────────────────────────────┐
            ▼              ▼                             ▼
mediateca-madrid-enrich   mediateca-madrid (API)   frontend
  crawler/parser            FastAPI solo lectura      Next.js
  repositorio de escritura  /api/search               tipos generados
  worker/scheduler          /api/records
  migraciones               /api/libraries
  escritura de índice       /health
            │
            ▼
   PostgreSQL compartido  ◄──── API solo lectura
   Meilisearch compartido ◄──── API solo lectura
```

## Flujo de datos

1. **Descubrimiento**: enrich consulta el OPAC y crea stubs con cursor y marcas de progreso.
2. **Enriquecimiento**: enrich descarga cada ficha, normaliza metadatos y ejemplares y actualiza PostgreSQL.
3. **Indexación**: enrich actualiza Meilisearch al terminar cada lote.
4. **Lectura**: la API consulta PostgreSQL para fichas y bibliotecas, y Meilisearch para búsqueda y facetas.
5. **Portal**: Next.js consume la API; no accede directamente a la base ni al índice.

## Propiedad de escritura

| Componente | PostgreSQL | Meilisearch |
|---|---|---|
| `mediateca-madrid-enrich` | Escritura, migraciones y `schema_meta` | Escritura del índice |
| `mediateca-madrid` | Solo lectura | Solo lectura |
| `mediateca-madrid-shared` | Modelos y contratos | Contrato de documentos |

## Modelo de datos compartido

El modelo obra → edición → ejemplar, las marcas de progreso (`is_stub`, `discovery_seen_at`, `detail_fetched_at`, `missing_at`), los países de origen de TMDB (`paises_origen`), la cola `harvest_jobs` y `schema_meta` viven en `mediateca_shared.models`. La API los consume en modo lectura con el wheel `mediateca-shared` `0.2.0` y el esquema `2`.

## Despliegue

- `mediateca-madrid-enrich` despliega PostgreSQL, Meilisearch, worker y scheduler, y crea la red Docker `mediateca`.
- `mediateca-madrid` despliega API y portal y se une a esa red externa.
- Orden de despliegue: shared → enrich (migraciones) → app.
- La API comprueba `schema_meta.schema_version` al arrancar y falla si no coincide con `SCHEMA_VERSION`.

## Búsqueda de solo lectura

La app usa un adaptador `CatalogSearch` sobre Meilisearch. No escribe documentos, no crea el índice y no reconstruye facetas por su cuenta.

El índice publica `paises_origen` como atributo filtrable y faceta. `GET /api/search` acepta el parámetro repetible `paises_origen` con códigos ISO 3166-1 alfa-2 y lo combina con la consulta y el resto de filtros; `GET /api/records/{titn}` devuelve `paises_origen` junto al `pais` bibliográfico del OPAC. Los países proceden de TMDB y solo están disponibles tras la migración, el backfill y la reindexación de `mediateca-madrid-enrich`.

## Contratos

`mediateca-madrid-shared` publica los esquemas Pydantic y el `openapi.json`. El portal genera sus tipos TypeScript desde ese contrato; la CI falla si el contrato y los tipos no coinciden.

## Decisiones

- **Tres repositorios**: separan el ciclo de vida de ingesta y portal y evitan que la API escriba el catálogo.
- **PostgreSQL como fuente de verdad**: el índice es reconstruible por enrich.
- **Sin Alembic**: migraciones SQL idempotentes en enrich y `schema_meta` para compatibilidad.
- **Sin base propia para la app**: ambos servicios comparten PostgreSQL y Meilisearch.
