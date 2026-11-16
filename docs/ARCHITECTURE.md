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
3. **Directorio**: `mediateca refresh-branches` lee el Directorio de Bibliotecas de la Comunidad de Madrid y completa direccion, codigo postal y coordenadas de las sucursales.
4. **Indexacion**: enrich actualiza Meilisearch al terminar cada lote.
5. **Lectura**: la API consulta PostgreSQL para fichas y bibliotecas, y Meilisearch para busqueda y facetas.
6. **Portal**: Next.js consume la API; no accede directamente a la base ni al indice. La ordenacion por cercania se calcula en el cliente a partir del codigo postal elegido.

## Propiedad de escritura

| Componente | PostgreSQL | Meilisearch |
|---|---|---|
| `services/enrich` | Escritura, migraciones y `schema_meta` | Escritura del indice |
| `services/api` | Solo lectura | Solo lectura |
| `apps/web` | Sin acceso directo | Sin acceso directo |
| `packages/shared` | Modelos y contratos | Contrato de documentos |

## Modelo de datos compartido

El modelo obra -> edicion -> ejemplar, las marcas de progreso, los paises de origen de TMDB, la cola `harvest_jobs` y `schema_meta` viven en `packages/shared/src/mediateca_shared`. La API y la ingesta instalan el paquete local; no hay wheels ni copias versionadas.

## Sucursales y ubicaciones

La tabla `sucursales` guarda una ficha por sucursal con `codigo` unico, biblioteca, nombre, municipio, direccion, codigo postal y coordenadas opcionales. `Ejemplar` se relaciona con su sucursal por `sucursal_codigo` mediante una relacion de solo lectura, sin clave foranea ni relleno retroactivo. `Biblioteca.codigo_postal` y el resto de campos de ubicacion sirven de respaldo cuando un ejemplar no tiene sucursal.

`SCHEMA_VERSION` es `5`. La migracion `services/enrich/scripts/migrate_sucursales_geo.sql` crea la tabla, anade la columna y actualiza `schema_meta`; es idempotente y se aplica desde `make migrate`. En bases nuevas, `Base.metadata.create_all` crea el esquema.

La API expone `EjemplarOut.ubicacion` con codigo postal, municipio, latitud y longitud. El portal usa esos datos y, si faltan coordenadas de sucursal, el centroide del codigo postal del JSON `apps/web/lib/codigos-postales-madrid.json`. Ese JSON se genera con `scripts/generate_codigos_postales.py` a partir de centroides abiertos y del municipio del INE; no se sirve desde PostgreSQL ni desde Meilisearch.

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
