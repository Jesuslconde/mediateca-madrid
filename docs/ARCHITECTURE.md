# Arquitectura

## Monorepo

```text
packages/shared
  modelos SQLAlchemy + esquemas Pydantic + openapi.json + SCHEMA_VERSION
            │
            ├──────────────────────────────┐
            ▼                              ▼
services/enrich                  services/api + apps/web
  crawler/parser                   FastAPI solo lectura
  repositorio de escritura         Next.js
  worker/scheduler                 tipos generados
  dashboard
  migraciones
            │                              │
            ▼                              ▼
   PostgreSQL compartido  ◄──── API solo lectura
   Meilisearch compartido ◄──── API solo lectura
```

## Flujo de datos

1. **Descubrimiento**: enrich consulta el OPAC y crea stubs con cursor y marcas de progreso.
2. **Enriquecimiento**: enrich descarga cada ficha, normaliza metadatos y ejemplares y actualiza PostgreSQL.
3. **Indexacion**: enrich actualiza Meilisearch al terminar cada lote.
4. **Lectura**: la API consulta PostgreSQL para fichas y bibliotecas, y Meilisearch para busqueda y facetas.
5. **Portal**: Next.js consume la API; no accede directamente a la base ni al indice.

## Propiedad de escritura

| Componente | PostgreSQL | Meilisearch |
|---|---|---|
| `services/enrich` | Escritura, migraciones y `schema_meta` | Escritura del indice |
| `services/api` | Solo lectura | Solo lectura |
| `apps/web` | Sin acceso directo | Sin acceso directo |
| `packages/shared` | Modelos y contratos | Contrato de documentos |

## Modelo de datos compartido

El modelo obra -> edicion -> ejemplar, las marcas de progreso, los paises de origen de TMDB, la cola `harvest_jobs` y `schema_meta` viven en `packages/shared/src/mediateca_shared`. La API y la ingesta instalan el paquete local; no hay wheels ni copias versionadas.

## Imagenes

| Imagen | Servicios |
|---|---|
| `mediateca-batch` | `init`, `worker`, `dashboard`, `scheduler` |
| `mediateca-web` | `api`, `web` |

La imagen `mediateca-web` contiene Python y Node. La API y el portal se ejecutan como contenedores separados para mantener el aislamiento de procesos.

## Despliegue

- `docker-compose.yml` levanta el stack completo en local.
- `deploy/portainer-stack.yml` usa las imagenes publicadas en el registry.
- El orden es `db/meilisearch -> init -> batch/web`.
- La API comprueba `schema_meta.schema_version` al arrancar y falla si no coincide con `SCHEMA_VERSION`.

## Busqueda de solo lectura

La API usa un adaptador `CatalogSearch` sobre Meilisearch. No escribe documentos, no crea el indice y no reconstruye facetas por su cuenta.

El indice publica `paises_origen` como atributo filtrable y faceta. `GET /api/search` acepta el parametro repetible `paises_origen` y lo combina con la consulta y el resto de filtros; `GET /api/records/{titn}` devuelve `paises_origen` junto al `pais` bibliografico del OPAC.

## Contratos

`services/api` genera `contracts/openapi.json`. El portal genera sus tipos TypeScript desde ese contrato con `make contracts`.

## Decisiones

- **Un monorepo**: una sola fuente de modelos y un unico ciclo de release.
- **Dos imagenes**: reduce builds y despliegues sin mezclar los procesos de ingesta con los de lectura.
- **PostgreSQL como fuente de verdad**: el indice es reconstruible por enrich.
- **Sin Alembic**: migraciones SQL idempotentes en enrich y `schema_meta` para compatibilidad.
- **Sin base propia para la app**: API y portal leen del mismo PostgreSQL y Meilisearch.
