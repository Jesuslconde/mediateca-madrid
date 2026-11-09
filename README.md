# Mediateca Madrid

Portal alternativo de búsqueda de vídeos, DVD y Blu-ray de las bibliotecas públicas de la Comunidad de Madrid.

El OPAC oficial (AbsysNet) no ofrece una API pública ni facetas que distingan DVD de Blu-ray, dirección, reparto, duración o bibliotecas tenedoras. Este proyecto recolecta los metadatos públicos, los normaliza, los indexa y los expone con una API y un portal propio.

## Qué incluye

- Recolector del OPAC con gestión de sesión, paginación, rate limit y snapshots HTML.
- Parser de fichas HTML/MARC 21.
- Detección normalizada de soportes: `DVD`, `Blu-ray`, `4K UHD`, `VHS` y `Varios`.
- Modelo de datos obra → edición → ejemplar.
- Índice de búsqueda con facetas en Meilisearch.
- API REST con búsqueda, facetas, fichas y bibliotecas.
- Portal Next.js con filtros de soporte, género, año, idioma y biblioteca.
- Docker Compose con PostgreSQL, Meilisearch, API, scheduler y frontend.
- Especificaciones y tareas gestionadas con **OpenSpec**.

## Arquitectura

```text
OPAC AbsysNet
     │ HTTPS + sesión
     ▼
 Crawler ──► snapshots HTML ──► Parser ──► normalización
                                               │
                                               ▼
                                         PostgreSQL
                                         (fuente de verdad)
                                               │
                              ┌────────────────┴────────────────┐
                              ▼                                 ▼
                        Meilisearch                       API FastAPI
                        (índice/facetas)                        │
                                                                ▼
                                                          Portal Next.js
```

Más detalle en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Inicio rápido

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env
make up
make init
make demo
```

Abre:

- Portal: <http://localhost:3000>
- API: <http://localhost:8000/docs>
- Meilisearch: <http://localhost:7700>

`make demo` carga dos fichas de ejemplo (la misma película en DVD y en Blu-ray) e indexa el resultado. No toca el OPAC.

### Actualizar una instalación existente

Si vienes de una versión que guardaba disponibilidad de préstamo, elimina esas columnas y reindexa:

```bash
make migrate-disponibilidad
docker compose exec api mediateca index --reset
```

### Ingesta real

```bash
make harvest q=cine pages=2 limit=20
make index
```

O directamente en el contenedor:

```bash
docker compose exec api mediateca harvest --query cine --max-pages 2 --limit 20
docker compose exec api mediateca index
```

El recolector aplica un retardo configurable (`MEDIATECA_CRAWL_DELAY`) y no intenta eludir reCAPTCHAs. Si el OPAC los solicita, detiene la recolección.

### Scheduler

```bash
docker compose --profile jobs up -d scheduler
```

Ejecuta una recolección periódica de fichas para actualizar metadatos y la lista de bibliotecas. Configurable con `MEDIATECA_SCHEDULER_HARVEST_HOURS`.

## Comandos útiles

```bash
make help
make logs
make ps
make test
make migrate-disponibilidad
make shell
make psql
make clean
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado de PostgreSQL y Meilisearch |
| GET | `/api/search` | Búsqueda con `q`, `soporte`, `genero`, `anio_desde`, `anio_hasta`, `idioma`, `biblioteca`, `page`, `limit`, `sort` |
| GET | `/api/records/{titn}` | Ficha completa con ejemplares |
| GET | `/api/libraries` | Bibliotecas con número de ejemplares |
| GET | `/api/stats` | Totales y reparto por soporte |

Ejemplos:

```bash
curl "http://localhost:8000/api/search?q=abejas&soporte=DVD&soporte=Blu-ray"
curl "http://localhost:8000/api/search?soporte=Blu-ray&limit=5"
curl "http://localhost:8000/api/records/2101557"
```

## Estructura

```text
backend/
  src/mediateca/
    api/          FastAPI, routers y schemas
    catalog/      modelos, parser, soportes, repositorio, crawler, indexer
    core/         configuración, base de datos, logging y cliente Meilisearch
  fixtures/       fichas HTML de ejemplo (DVD y Blu-ray)
  tests/          pytest
frontend/
  app/            páginas Next.js (inicio, búsqueda, ficha)
  components/     buscador, tarjetas, facetas, bibliotecas
  lib/            cliente de la API y utilidades
openspec/         especificaciones y cambios
docs/             arquitectura
```

## Datos y limitaciones

- La fuente es el catálogo público de AbsysNet. No hay Z39.50/SRU/OAI público en el catálogo de Madrid; la ingesta se hace por HTTP.
- El HTML puede cambiar. Los selectores están centralizados en `backend/src/mediateca/catalog/parser.py` y cubiertos por tests con fixtures.
- La ficha muestra las bibliotecas que poseen cada título y enlaza al OPAC para consultar el estado de préstamo, que no se refresca de forma continua.
- No se almacenan datos personales, solo metadatos bibliográficos y de ejemplares.
- Antes de publicar un portal en producción, revisa las condiciones de reutilización de los metadatos y atribuye la fuente.

## OpenSpec

El proyecto usa OpenSpec para gestionar especificaciones y metas. El MVP está archivado y sus capacidades viven en `openspec/specs/`:

```bash
openspec list --specs
openspec show ingesta-catalogo
openspec show filtro-soporte
openspec show portal-web
openspec view
```

El cambio original está en `openspec/changes/archive/2026-11-09-mvp-catalogo-video/`. Para la siguiente meta, crea un cambio nuevo con `openspec new change <nombre>` y consulta el roadmap.

## Licencia

Este proyecto se distribuye bajo la **PolyForm Noncommercial License 1.0.0**. Puedes usar, copiar, modificar y distribuir el software **para fines no comerciales**, siempre que mantengas el aviso de copyright, el texto de la licencia y des crédito al proyecto original. Consulta [`LICENSE`](LICENSE).

No está permitido vender el código, usarlo con fines comerciales ni sublicenciarlo comercialmente. Cualquier distribución debe ser gratuita y acompañarse de esta misma licencia. La licencia no cubre los metadatos del catálogo ni contenidos de terceros.

**Nota:** por esta restricción comercial, esta licencia es *source-available* y no cumple la definición de open source de la OSI.

### Créditos

- Proyecto original: [Mediateca Madrid](https://github.com/Jesuslconde/mediateca-madrid), creado por [Jesuslconde](https://github.com/Jesuslconde).
- Los metadatos del catálogo proceden de las Bibliotecas de la Comunidad de Madrid y no están cubiertos por esta licencia.
- Las portadas, sinopsis, enlaces externos y demás contenidos de terceros pertenecen a sus respectivos titulares.

## Roadmap

Consulta [`ROADMAP.md`](ROADMAP.md).
