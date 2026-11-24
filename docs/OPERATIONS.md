# Operación y despliegue

Esta guía reúne los procedimientos que afectan a varios módulos. La documentación interna de cada componente está en:

- [`services/api/README.md`](../services/api/README.md): API pública y listas de favoritos.
- [`services/enrich/README.md`](../services/enrich/README.md): ingesta, cola, indexación y dashboard.
- [`apps/web/README.md`](../apps/web/README.md): portal Next.js.
- [`packages/shared/README.md`](../packages/shared/README.md): modelo persistente y contratos compartidos.

## Arquitectura del stack

El sistema se ejecuta en dos imágenes Docker:

| Imagen | Servicios | Contenido principal |
|---|---|---|
| `mediateca-batch` | `init`, `worker`, `dashboard`, `scheduler` | Python 3.12, `services/enrich` y `packages/shared` |
| `mediateca-web` | `api`, `web` | API Python, portal Next.js standalone y `packages/shared` |

`db/meilisearch -> init -> worker/dashboard/scheduler/api -> web` es el orden de arranque definido por `docker-compose.yml`. PostgreSQL y Meilisearch usan volúmenes independientes. El volumen `worker_heartbeat` lo comparten el worker y el dashboard.

La API y el portal no acceden directamente a PostgreSQL o Meilisearch. La API consulta ambos almacenamientos; el portal llama a la API. La ingesta es la propietaria de las migraciones y de las escrituras del catálogo. La única escritura de la API fuera del catálogo son las listas de favoritos.

## Preparación del entorno

Requisitos:

- Docker Engine y Docker Compose.
- GNU Make.
- Node.js 22 y npm para tareas locales del portal o generación de tipos.
- Python 3.11–3.14 para desarrollo local de los paquetes Python.

Copia la plantilla y revisa los valores sensibles antes de arrancar:

```bash
cp .env.example .env
make up
```

Servicios locales predeterminados:

| Servicio | URL |
|---|---|
| Portal | <http://localhost:3000> |
| API y documentación OpenAPI | <http://localhost:8000/docs> |
| Dashboard de ingesta | <http://localhost:8080> |
| Meilisearch | <http://localhost:7700> |

El servicio `init` de Compose ejecuta `python -m mediateca init`: crea las tablas que faltan, aplica todas las migraciones `migrate_*.sql` por orden lexicográfico, elimina listas caducadas y reconstruye el índice si la versión anterior del esquema es menor o no existe.

## Comandos frecuentes

```bash
make help                 # Catálogo de objetivos disponibles
make up                   # Construir y levantar el stack
make down                 # Detener sin borrar volúmenes
make ps                   # Estado de contenedores
make logs                 # Logs de todos los servicios
make worker-logs          # Logs del worker
make dashboard-logs       # Logs del dashboard
make init                 # Ejecutar inicialización en un contenedor temporal
make migrate              # Aplicar migraciones idempotentes
make psql                 # Abrir psql
```

Parámetros de `Makefile`: `q`, `pages`, `limit`, `fuente` y `branches_limit`.

### Ingesta y catálogo

```bash
make harvest q=cine pages=2 limit=20
make harvest q=cine pages=2 limit=20 fuente=andalucia
make branches
make branches branches_limit=20 fuente=madrid
make branches-enqueue
make index
make index-reset
```

- `harvest` ejecuta una búsqueda concreta y descarga las fichas de detalle.
- `discover` se usa para enumerar el catálogo y crear stubs; no es el objetivo de `make harvest`.
- `branches` ejecuta el directorio de bibliotecas de forma síncrona.
- `branches-enqueue` crea un trabajo `branches` para que lo ejecute el worker.
- `index` reconstruye los documentos desde PostgreSQL sin borrar previamente el índice.
- `index-reset` borra el índice y lo reconstruye; reservarlo para cambios de esquema o reparaciones.

La web pública filtra siempre por `detail_complete=true`; los stubs descubiertos no aparecen como fichas completas.

### Contratos y calidad

```bash
make openapi              # Exportar contracts/openapi.json
make web-types            # Generar apps/web/lib/api-types.ts
make contracts            # openapi + web-types
make check-schema         # Comprobar SCHEMA_VERSION en la base
make test                 # shared + API + enrich
make test-shared
make test-api
make test-enrich
make test-migrations      # Aplica y repite migraciones sobre PostgreSQL
make lint                 # Ruff sobre API, enrich y shared
make fmt                  # Formateo con Ruff
```

Las pruebas Python se ejecutan dentro de las imágenes para respetar los entornos y dependencias de cada paquete. `test-migrations` levanta PostgreSQL y comprueba la idempotencia de las migraciones.

## Migraciones y versiones del esquema

Las migraciones están en [`services/enrich/scripts`](../services/enrich/scripts) y se ejecutan con `psycopg` mediante `conn.exec_driver_sql`. No se usa Alembic. Cada script debe poder ejecutarse más de una vez sin error y actualizar `schema_meta` cuando corresponda.

Al cambiar el modelo compartido:

1. Modificar [`packages/shared`](../packages/shared).
2. Añadir o ajustar la migración SQL equivalente.
3. Actualizar `SCHEMA_VERSION` si cambia el contrato persistente.
4. Regenerar OpenAPI y tipos si cambia la API.
5. Ejecutar `make test-migrations`, `make build` y el despliegue.

La API comprueba al arrancar que el valor de `schema_meta` con `key='schema_version'` coincide con `SCHEMA_VERSION`; si no, falla con un error explícito. `init` aplica las migraciones antes de arrancar API y worker.

## Indexación y recuperación

La indexación normal es incremental y se ejecuta por `record_id` en lotes de 200 documentos. Si Meilisearch falla, los identificadores pendientes quedan en `harvest_jobs.stats.pending_index_titns` y se reintentan antes de continuar el trabajo.

Después de cambiar campos filtrables, facetas, ordenación o la estructura de documentos:

```bash
make migrate
make index-reset
```

Un fallo de Meilisearch no revierte una agrupación manual ya confirmada en PostgreSQL. En ese caso, el dashboard avisa y se puede reparar con `make index` o `make index-reset`.

## Publicación de imágenes

La versión del release se centraliza en [`VERSION`](../VERSION). `scripts/bump-version.sh` actualiza ese archivo, los tres `pyproject.toml`, los `__version__` de los paquetes Python y `apps/web/package.json`/`package-lock.json`.

Publicación completa:

```bash
make bump-release type=fix
```

También acepta `type=minor` y `type=major`. El script incrementa la versión, construye las dos imágenes y publica cada una con la etiqueta de versión y `latest`.

```bash
REGISTRY=otro.registro:5000 ./scripts/bump-release.sh minor --no-cache
```

El registro predeterminado de los scripts es `192.168.1.169:5000`. Se puede cambiar con `REGISTRY`; `BATCH_IMAGE` y `WEB_IMAGE` permiten cambiar los nombres. Para separar los pasos:

```bash
make bump type=minor
make release
```

## Portainer

[`deploy/portainer-stack.yml`](../deploy/portainer-stack.yml) usa imágenes publicadas en lugar de construir desde el contexto. Configura al menos:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- `MEILI_MASTER_KEY`.
- `MEDIATECA_REGISTRY` y `MEDIATECA_IMAGE_TAG`.
- `MEDIATECA_API_CORS_ORIGINS` con el origen público del portal.
- `MEDIATECA_DASHBOARD_ADMIN_TOKEN` si el dashboard es accesible desde una red no confiable.
- `MEDITECA_WEB_COOKIE_SECURE=true` cuando haya TLS y el proxy no reenvíe `x-forwarded-proto`.

A diferencia de Compose, el `init` de Portainer ejecuta por separado `init-db`, `migrate`, `clean-lists` e `index`. No usa el atajo `python -m mediateca init` ni su detección automática de salto de esquema.

No publiques el dashboard sin autenticación. Aunque valida el esquema de las URLs de FlareSolverr y rechaza credenciales incrustadas, una URL editable puede usarse para alcanzar servicios internos (SSRF).

## Cookies y proxies

La cookie de la lista activa del portal admite:

- `auto`: añade `Secure` si la petición llega por HTTPS o con `x-forwarded-proto: https`.
- `true`: fuerza `Secure`.
- `false`: no añade `Secure`; solo apropiado para despliegues HTTP.

El token de administración del dashboard se guarda en una cookie `HttpOnly` con `SameSite=Strict` y una vigencia de ocho horas. Debe viajar sobre HTTPS en producción.

## Copias de seguridad

Antes de una migración destructiva o de un `index-reset`, respalda:

- El volumen `postgres_data`.
- El volumen `meili_data` si se quiere conservar el índice; puede reconstruirse desde PostgreSQL.
- La configuración sensible de `.env` y del stack de Portainer.

`make clean` ejecuta `docker compose down -v` y borra los volúmenes: es destructivo y no debe usarse como parada rutinaria.

## Datos, atribución y licencia

- Las fichas proceden de catálogos públicos AbsysNet. La recolección se ejecuta en `services/enrich`.
- Las direcciones y coordenadas de sucursales proceden del Directorio de Bibliotecas de la Comunidad de Madrid o del directorio abierto de la Junta de Andalucía, según la fuente.
- Los centroides de códigos postales usan `kodens-dev/Spain-Postal-Codes` (MIT); los municipios proceden del INE mediante `regi-es/ds-codigos-postales-ine-es` (CC BY 4.0). El portal muestra esta atribución.
- Las portadas, sinopsis y enlaces de TMDB pertenecen a sus titulares. Este producto usa la API de TMDB, pero no está avalado ni certificado por TMDB.
- No se almacenan datos personales. Las listas guardan identificadores de ediciones, un título opcional y marcas de tiempo; la ubicación elegida para ordenar por cercanía vive solo en `localStorage`.

El software se distribuye bajo **PolyForm Noncommercial License 1.0.0**. Consulta [`LICENSE`](../LICENSE). La licencia no cubre metadatos del catálogo ni contenidos de terceros.

Proyecto original: [Mediateca Madrid](https://github.com/Jesuslconde/mediateca-madrid), creado por [Jesuslconde](https://github.com/Jesuslconde).
