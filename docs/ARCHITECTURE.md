# Arquitectura

Mediateca Madrid es un monorepo con cuatro módulos de software y una capa de despliegue. PostgreSQL es la fuente de verdad del catálogo; Meilisearch es un índice reconstruible; el portal consume exclusivamente la API.

## Módulos

| Módulo | Responsabilidad | Documentación |
|---|---|---|
| `packages/shared` | Modelos SQLAlchemy, esquemas Pydantic, identidad y `SCHEMA_VERSION` | [`README`](../packages/shared/README.md) |
| `services/enrich` | Descubrimiento, enriquecimiento, migraciones, cola, índice y dashboard | [`README`](../services/enrich/README.md) |
| `services/api` | Búsqueda, fichas, estadísticas y listas de favoritos | [`README`](../services/api/README.md) |
| `apps/web` | Portal Next.js y Server Actions | [`README`](../apps/web/README.md) |

```text
                         ┌──────────────────────┐
                         │   Catálogos OPAC     │
                         └──────────┬───────────┘
                                    │ HTTP
                         ┌──────────▼───────────┐
                         │ services/enrich      │
                         │ discover / enrich    │
                         │ worker / scheduler   │
                         └──────┬────────┬──────┘
                                │        │
                     PostgreSQL │        │ Meilisearch
                                │        │
                         ┌──────▼────────▼──────┐
                         │ services/api         │
                         │ búsqueda + fichas    │
                         │ listas               │
                         └──────────┬──────────┘
                                    │ HTTP API_URL
                         ┌──────────▼───────────┐
                         │ apps/web             │
                         │ Server Components    │
                         │ Server Actions       │
                         └──────────────────────┘
```

## Propiedad de escrituras

| Componente | PostgreSQL | Meilisearch |
|---|---|---|
| `services/enrich` | Migraciones y escritura del catálogo, cola y configuración | Creación, settings y escritura |
| `services/api` | Lectura del catálogo; escritura solo en `listas` y `lista_items` | Solo lectura |
| `apps/web` | Sin acceso directo | Sin acceso directo |
| `packages/shared` | Define modelos y esquemas | Define el subconjunto público mediante el indexador de ingesta |

La expresión “API de solo lectura” se aplica al catálogo y al índice. Las listas de favoritos son una excepción explícita y acotada.

## Flujo de datos

1. **Descubrimiento**: `enrich` enumera resultados AbsysNet y crea stubs con metadatos básicos.
2. **Enriquecimiento**: descarga fichas completas, normaliza MARC, soportes, personas, materias, enlaces y ejemplares.
3. **TMDB**: opcionalmente añade países de origen, ID, portada y enlace sin sobrescribir el país del OPAC.
4. **Directorio**: actualiza bibliotecas y sucursales con el directorio de cada fuente.
5. **Indexación**: construye documentos Meilisearch desde PostgreSQL, de forma incremental o completa.
6. **Búsqueda**: la API consulta Meilisearch, agrupa por obra y completa agregados desde PostgreSQL.
7. **Portal**: Next.js renderiza los resultados y gestiona favoritos mediante la API.

La web pública impone `detail_complete=true`; los stubs no aparecen como fichas completas.

## Identidad y fuentes

La identidad de una edición es:

```text
record_id = <fuente>:<titn>
```

La unicidad de TITN es por fuente. Bibliotecas y sucursales son únicas por `(fuente_id, codigo)`; los ejemplares por `(fuente_id, external_key)`.

`Fuente` almacena URL, ruta, patrón de sesión, campo y valor de formato, retardo, estado y `options`. Las opciones controlan descubrimiento avanzado/novedades, detalle durante descubrimiento, TLS, cobertura y directorio.

Madrid y Andalucía están habilitadas tras los seeds. Las diez fuentes autonómicas y las cinco fuentes CCBIP se siembran deshabilitadas. Deshabilitar una fuente no borra sus datos ni altera las demás.

## Modelo persistente

El núcleo es:

```text
Fuente ──< Edición >── Obra
            │
            ├──< Ejemplar >── Biblioteca ──< Sucursal
            ├──< EdicionPersona >── Persona
            ├──< EdicionMateria >── Materia
            └──< Enlace
```

También existen:

- `harvest_jobs` y `harvest_runs` para ingesta.
- `app_config` para configuración persistida, definida en `services/enrich`.
- `schema_meta` para la versión del esquema.
- `listas` y `lista_items` para favoritos.

`SCHEMA_VERSION` está actualmente en `8`. La API lo comprueba al arrancar y aborta si no coincide. Las migraciones SQL idempotentes viven en `services/enrich/scripts`; no se usa Alembic.

### Ubicaciones

`Ejemplar` guarda `sucursal_codigo`, pero no tiene FK directa a `Sucursal`. La relación ORM es de solo lectura y se resuelve por fuente y código. La API devuelve ubicación de sucursal si existe; si no, usa biblioteca; si no hay datos, devuelve `null`.

El portal usa coordenadas de la API y, como respaldo, centroides de códigos postales madrileños versionados en `apps/web/lib/codigos-postales-madrid.json`. La distancia se calcula en cliente con Haversine.

## Cola y concurrencia

`harvest_jobs` admite cinco tipos: `discover`, `enrich`, `index`, `tmdb` y `branches`.

El worker:

- Usa entre 1 y 5 hilos.
- Reclama con `FOR UPDATE SKIP LOCKED`.
- Serializa el reclamo con `pg_advisory_xact_lock`.
- Respeta conflictos por fuente.
- Marca heartbeat por trabajo y de worker.
- Recupera trabajos `running` estancados.
- Reencola errores y no consume intentos cuando hay CAPTCHA.

Para una misma fuente no pueden coincidir el mismo tipo ni las parejas `discover/enrich`, `enrich/tmdb`, `enrich/index` y `tmdb/index`. `branches` es compatible con todos. Un indexado global sin fuente es exclusivo.

El scheduler no ejecuta OPAC: solo encola descubrimiento, enriquecimiento y reconciliación según `app_config`.

## Indexación

`MeiliIndexer` pertenece a `services/enrich`. La API solo lee el índice.

El documento Meilisearch incluye:

- Identidad y fuente.
- Obra y `obra_key`.
- Bibliografía, personas, materias y soportes.
- Bibliotecas y ubicaciones.
- Países de origen, portada y enlace TMDB.
- `detail_complete`, `is_stub` y `updated_at`.

Clave primaria: `id`, derivada de `record_id`. La agrupación usa `obra:<id>` o `edicion:<record_id>`.

La indexación incremental usa lotes de 200 y conserva pendientes en `harvest_jobs.stats.pending_index_titns` si falla. `index` sin reset no elimina documentos huérfanos; `index --reset` vacía y reconstruye.

## Lectura y búsqueda

`CatalogSearch` ejecuta dos consultas Meilisearch:

1. Resultados paginados con `distinct="obra_key"`.
2. Totales y facetas sin agrupar.

Después, la API consulta PostgreSQL para agregar ediciones de cada obra: soportes, bibliotecas, ejemplares y metadatos de respaldo.

No hay búsqueda de fallback en PostgreSQL. Si Meilisearch falla, `/api/search` devuelve 503.

## Listas de favoritos

Las listas son el único dato escrito por la API:

- Token opaco generado con `secrets.token_urlsafe(24)`.
- Solo se guarda su SHA-256.
- Máximo 200 elementos.
- Caducidad de 180 días desde la última mutación efectiva.
- Elementos con snapshot de título si desaparece la edición.
- Sin cuentas ni datos personales.

El portal recuerda la lista activa en una cookie `HttpOnly`. Compartir `/lista/{token}` equivale a compartir permiso de lectura y edición. La limpieza de listas caducadas la ejecuta `services/enrich`.

## Contratos

La API genera [`contracts/openapi.json`](../contracts/openapi.json). El portal genera `apps/web/lib/api-types.ts` con `openapi-typescript`.

```bash
make openapi
make web-types
make contracts
```

El portal no importa modelos compartidos ni accede a almacenamientos.

## Ejecución y despliegue

Dos imágenes:

| Imagen | Servicios |
|---|---|
| `mediateca-batch` | `init`, `worker`, `dashboard`, `scheduler` |
| `mediateca-web` | `api`, `web` |

Compose ejecuta `python -m mediateca init`, que crea esquema, aplica migraciones, limpia listas y reconstruye el índice si baja la versión del esquema.

Portainer ejecuta `init-db`, `migrate`, `clean-lists` e `index` por separado. No aplica el reset condicional; los cambios que exijan reconstrucción completa requieren una acción explícita.

PostgreSQL y Meilisearch usan volúmenes independientes. El worker y el dashboard comparten el volumen de heartbeat.

## Decisiones

- **Monorepo**: una sola fuente de modelos y un ciclo de release.
- **Dos imágenes**: separan procesos de ingesta y lectura sin duplicar el modelo compartido.
- **PostgreSQL como verdad**: el índice se reconstruye.
- **Migraciones SQL idempotentes**: sin Alembic, con `schema_meta` para compatibilidad.
- **API como frontera**: el portal no conoce las bases de datos.
- **Cola persistente**: scheduler, dashboard y CLI comparten `harvest_jobs`.
- **Sin snapshots**: la ingesta actual solo persiste datos normalizados.

## Documentación

- [`docs/README.md`](README.md)
- [`OPERATIONS.md`](OPERATIONS.md)
- [`ARCHITECTURE_ENRICH.md`](ARCHITECTURE_ENRICH.md)
- [`CUTOVER.md`](CUTOVER.md)
- [`MIGRATION_INVENTORY.md`](MIGRATION_INVENTORY.md)
