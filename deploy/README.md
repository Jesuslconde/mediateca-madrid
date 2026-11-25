# Despliegue con Portainer

`deploy/portainer-stack.yml` define el stack de producción para Portainer. Consume imágenes prepublicadas; no construye el código durante el despliegue.

La guía de arranque, publicación y copias de seguridad está en [`docs/OPERATIONS.md`](../docs/OPERATIONS.md).

## Imágenes

```text
${MEDIATECA_REGISTRY}/mediateca-batch:${MEDIATECA_IMAGE_TAG}
${MEDIATECA_REGISTRY}/mediateca-web:${MEDIATECA_IMAGE_TAG}
```

- `mediateca-batch`: `init`, `worker`, `dashboard` y `scheduler`.
- `mediateca-web`: `api` y `web`.

El registro predeterminado es `192.168.1.169:5000` y la etiqueta predeterminada es `latest`. Para un despliegue reproducible se recomienda fijar una versión publicada en lugar de usar `latest`.

## Variables necesarias

| Variable | Servicio | Notas |
|---|---|---|
| `POSTGRES_DB` | `db` y conexiones | Nombre de la base |
| `POSTGRES_USER` | `db` y conexiones | Usuario PostgreSQL |
| `POSTGRES_PASSWORD` | `db` y conexiones | Valor sensible |
| `MEILI_MASTER_KEY` | Meilisearch, API, worker | Clave maestra; no usar la de desarrollo |
| `MEDIATECA_REGISTRY` | Imágenes | Host y puerto del registro |
| `MEDIATECA_IMAGE_TAG` | Imágenes | Versión común de ambas imágenes |
| `MEDIATECA_API_CORS_ORIGINS` | `api` | Origen público del portal, separado por comas |
| `MEDIATECA_DASHBOARD_ADMIN_TOKEN` | `dashboard` | Token de escritura; vacío deja el dashboard abierto |
| `MEDITECA_WEB_COOKIE_SECURE` | `web` | `auto`, `true` o `false` |

También pueden definirse `API_PORT`, `WEB_PORT`, `MEILI_PORT`, `MEDIATECA_DASHBOARD_PORT`, `MEDIATECA_MEILISEARCH_INDEX`, `MEDIATECA_CRAWL_DELAY`, `MEDIATECA_WORKER_CONCURRENCY`, `MEDIATECA_SCHEDULER_ENABLED`, `MEDIATECA_TMDB_API_TOKEN` y `MEDIATECA_FLARESOLVERR_URL`, entre otras.

## Orden de arranque

```text
PostgreSQL + Meilisearch
          ↓
        init
          ↓
worker / dashboard / scheduler / API
          ↓
        web
```

`init` tiene `restart: "no"` y los demás servicios dependen de que termine correctamente. Su comando ejecuta:

```bash
python -m mediateca init-db
python -m mediateca migrate
python -m mediateca clean-lists
python -m mediateca index
```

A diferencia del servicio `init` de `docker-compose.yml`, esta secuencia no usa `python -m mediateca init`. Por tanto, no detecta automáticamente un salto de `SCHEMA_VERSION` para reconstruir el índice con `--reset`. Si una migración exige reindexado completo, debe ejecutarse de forma controlada durante el despliegue.

## Servicios

### `db`

- Imagen `postgres:16-alpine`.
- Healthcheck con `pg_isready`.
- Volumen `postgres_data`.
- No publica puerto en el stack de Portainer.

### `meilisearch`

- Imagen `getmeili/meilisearch:v1.12`.
- `MEILI_ENV=production` y analítica desactivada.
- Healthcheck contra `/health`.
- Volumen `meili_data`.
- Publica el puerto configurado por `MEILI_PORT`; puede mantenerse privado si solo lo consumen API e ingesta.

### `worker`

- Ejecuta `python -m mediateca worker`.
- Healthcheck basado en la antigüedad del archivo de heartbeat.
- Comparte `worker_heartbeat` con el dashboard.
- Recibe la configuración de OPAC, TMDB, FlareSolverr y concurrencia.

### `dashboard`

- Escucha en `0.0.0.0:8080` dentro del contenedor.
- Publica `MEDIATECA_DASHBOARD_PORT`.
- Healthcheck contra `/health`.
- Debe proteger el puerto con la red y el token de administración.

### `scheduler`

- Ejecuta `python -m mediateca scheduler`.
- Solo encola trabajos; no descarga fichas ni actualiza el índice directamente.

### `api`

- Imagen `mediateca-web`.
- Uvicorn en `0.0.0.0:8000`.
- Publica `API_PORT`.
- Comprueba `SCHEMA_VERSION` al arrancar.

### `web`

- Imagen `mediateca-web`.
- Servidor Next.js standalone en el puerto 3000.
- Consume `API_URL=http://api:8000`.
- Publica `WEB_PORT`.

## Red y volúmenes

Todos los servicios usan la red `mediateca`. Los nombres de servicio (`db`, `meilisearch`, `api`) son los hosts internos; no deben sustituirse por `localhost` en las URLs de contenedor.

| Volumen | Propósito |
|---|---|
| `postgres_data` | Catálogo, cola, configuración persistida y listas |
| `meili_data` | Índice de búsqueda |
| `raw_data` | Reservado; el enriquecimiento actual no escribe snapshots |
| `worker_heartbeat` | Señal de salud compartida por worker y dashboard |

## Seguridad

- Usa contraseñas y claves distintas de los valores de `.env.example`.
- Sirve el portal y la API detrás de HTTPS.
- Configura `MEDITECA_WEB_COOKIE_SECURE=true` si el proxy no reenvía `x-forwarded-proto`.
- Restringe el dashboard a una red confiable y define `MEDIATECA_DASHBOARD_ADMIN_TOKEN`.
- No expongas PostgreSQL ni Meilisearch públicamente si no es necesario.
- Revisa los términos de uso del OPAC antes de habilitar FlareSolverr.

## Actualización

1. Publica una nueva versión de ambas imágenes.
2. Actualiza `MEDIATECA_IMAGE_TAG` en el stack.
3. Revisa las migraciones incluidas y si requieren `index --reset`.
4. Redespliega y comprueba `init`, API, worker y dashboard.
5. Valida `/health`, `/api/health` y una búsqueda del portal.

No actualices solo una de las dos imágenes: API, portal e ingesta comparten el modelo y la versión del esquema.
