# Imágenes Docker

El repositorio construye dos imágenes a partir de la raíz del monorepo. Ambas incluyen `packages/shared` para que API e ingesta utilicen exactamente los mismos modelos y esquemas.

| Dockerfile | Imagen local | Servicios |
|---|---|---|
| `batch.Dockerfile` | `mediateca-batch:local` | `init`, `worker`, `dashboard`, `scheduler` |
| `web.Dockerfile` | `mediateca-web:local` | `api`, `web` |

## `batch.Dockerfile`

Base: `python:3.12-slim`.

Secuencia:

1. Instala `curl`, `libxml2` y `libxslt1.1`.
2. Copia `packages/shared` a `/app/packages/shared`.
3. Instala el paquete compartido.
4. Copia `.env.example`, el `pyproject.toml` y el `README` de ingesta.
5. Copia `src`, `scripts`, `fixtures` y `tests` de `services/enrich`.
6. Instala `services/enrich` en modo editable con el extra `dev`.
7. Define `python -m mediateca worker` como comando predeterminado.

Rutas importantes:

```text
/app/src/mediateca
/app/scripts/migrate_*.sql
/app/fixtures
/app/tests
/app/packages/shared
```

La imagen incluye herramientas de desarrollo porque los objetivos `make test-*`, `make lint` y `make fmt` ejecutan pytest y Ruff dentro de contenedores.

## `web.Dockerfile`

Es una construcción multi-etapa.

### Etapa `web-build`

- Base `node:22-bookworm-slim`.
- Instala dependencias con `npm ci`.
- Copia `apps/web`.
- Ejecuta `npm run build`.
- Aprovecha `output: "standalone"` de Next.js para producir un servidor autocontenido.

### Etapa `runtime`

- Base `node:22-bookworm-slim`.
- Instala Python 3, `venv`, `libpq5` y `curl`.
- Instala `packages/shared` en `/opt/venv`.
- Instala `services/api` en `/app/api` con sus dependencias de desarrollo.
- Copia el standalone de Next.js, los archivos estáticos y `public` a `/app/web`.
- Define `NODE_ENV=production`, `PORT=3000` y `HOSTNAME=0.0.0.0`.
- El comando predeterminado es `node server.js`.

La API se ejecuta en un contenedor independiente de la misma imagen con:

```bash
/opt/venv/bin/uvicorn mediateca.api.main:app --host 0.0.0.0 --port 8000
```

## Contexto y exclusión

Ambas construcciones usan `.` como contexto. `.dockerignore` excluye, entre otros:

- `.git`, `.opencode`, `docs` y `openspec`.
- `.env` y variantes, salvo `.env.example`.
- `node_modules`, `.next`, `out`, `dist`, `build`.
- Entornos virtuales, caches, bytecode y artefactos de empaquetado.
- Bases SQLite y datos locales.

No se copian secretos de `.env` a las imágenes. La configuración de runtime llega mediante variables de entorno de Compose o Portainer.

## Construcción local

```bash
make build
# o
docker compose build
```

También puede construirse cada imagen por separado:

```bash
docker build -f docker/batch.Dockerfile -t mediateca-batch:local .
docker build -f docker/web.Dockerfile -t mediateca-web:local .
```

## Publicación

`scripts/release.sh` construye y publica ambas imágenes con la versión de `VERSION` y `latest`. Usa Docker si está instalado y Podman como alternativa. `scripts/bump-release.sh` incrementa antes la versión.

```bash
make release
make bump-release type=minor
REGISTRY=otro.registro:5000 ./scripts/bump-release.sh fix --no-cache
```

El registro predeterminado es `192.168.1.169:5000`. Para más detalle, consulta [`docs/OPERATIONS.md`](../docs/OPERATIONS.md).

## Consideraciones

- La versión de Python del paquete permite 3.11–3.14, pero las imágenes fijan Python 3.12.
- El portal se compila con Node 22 y Next.js 16, y se ejecuta como servidor standalone; no usa `next start`.
- La imagen web contiene Python y Node porque aloja API y portal, aunque Compose los ejecuta en procesos separados.
- Una actualización debe publicar las dos imágenes con la misma versión para evitar incompatibilidades de modelo o esquema.
- `raw_data` se conserva en Compose y Portainer, pero el código actual no guarda HTML crudo.
