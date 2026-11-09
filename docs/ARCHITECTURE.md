# Arquitectura

## Flujo de datos

```text
                    ┌──────────────────────────┐
                    │   OPAC AbsysNet          │
                    │  ACC=131 / 161 / 165     │
                    └────────────┬─────────────┘
                                 │ HTTPS + sesión
                                 ▼
               ┌────────────────────────────────┐
               │  Crawler / Harvester           │
               │  - sesión y cookies            │
               │  - paginación                  │
               │  - reintentos/backoff          │
               └──────────────┬─────────────────┘
                              │ HTML / MARC
                              ▼
               ┌────────────────────────────────┐
               │  Snapshots en disco            │
               │  data/raw/<titn>-<fecha>.html  │
               └──────────────┬─────────────────┘
                              │
                              ▼
               ┌────────────────────────────────┐
               │  Parser + normalización        │
               │  - MARC 300$a, 245, 260...     │
               │  - personas y roles            │
               │  - DVD / Blu-ray               │
               │  - ejemplares por biblioteca   │
               └──────────────┬─────────────────┘
                              ▼
               ┌────────────────────────────────┐
               │  PostgreSQL                    │
               │  obras / ediciones / ejemplares│
               │  personas / materias / historial│
               └───────┬──────────────┬─────────┘
                       │              │
            indexación │              │ API REST
                       ▼              ▼
             ┌──────────────────┐  ┌──────────────────┐
             │ Meilisearch      │  │ FastAPI          │
             │ facetas y ranking│  │ búsqueda/fichas  │
             └──────────────────┘  └────────┬─────────┘
                                            ▼
                                     ┌──────────────────┐
                                     │ Next.js          │
                                     │ portal web       │
                                     └──────────────────┘
```

## Almacenamiento

| Componente | Guarda | ¿Fuente de verdad? |
|---|---|---|
| PostgreSQL | Obras, ediciones, ejemplares, personas, materias, bibliotecas | Sí |
| Meilisearch | Documentos denormalizados para búsqueda y facetas | No (reconstruible) |
| `data/raw` | HTML original de cada ficha | No, pero permite reprocesar |
| Memoria del proceso | Sesión del crawler | No |

## Modelo de datos

```text
obra
  id, titulo_uniforme, anio, director_principal

edicion
  id, titn, obra_id, titulo, titulo_uniforme, publicacion,
  anio, idioma, pais, duracion_min, edad_recomendada,
  sinopsis, generos, soportes, soporte_principal, ean,
  tipo_documento, notas, marc, source_url

ejemplar
  id, edicion_id, biblioteca_id, sucursal_codigo,
  sucursal_nombre, localizacion, signatura,
  tipo_ejemplar, soporte, external_key

persona
  id, nombre, nombre_normalizado

edicion_persona
  edicion_id, persona_id, rol, orden

materia
  id, termino

edicion_materia
  edicion_id, materia_id

biblioteca
  id, codigo, nombre, municipio, latitud, longitud

snapshot
  id, edicion_id, titn, url, path, sha256, fetched_at
```

## Detección de soporte

El OPAC etiqueta DVD y Blu-ray como «Videograbaciones (DVD)». El proyecto los distingue con dos señales:

1. `MARC 300$a` / «Descripción física»: `DVD-Video`, `Blu-ray`, `4K UHD`, `VHS`.
2. Campo `Soporte` de cada ejemplar: `Vídeo (DVD)`, `Vídeo (Blu-Ray)`, etc.

Las variantes `Blu-ray`, `Blu-Ray`, `BluRay`, `Blu ray` y `BD` se normalizan a `Blu-ray`. Una edición puede tener varios soportes (por ejemplo, un pack DVD + Blu-ray).

## Flujo de actualización

1. **Ingesta inicial**: consultas configuradas + paginación.
2. **Parseo y persistencia**: `UPSERT` por `TITN`.
3. **Indexación**: reconstrucción de documentos en Meilisearch.
4. **Incremental**: consultas de novedades o conjunto de consultas.
5. **Bibliotecas tenedoras**: cada recolección actualiza la lista de bibliotecas, sucursales, signaturas y soportes, sin comprobar préstamos.
6. **Reindexación**: tras cambios de esquema o reproceso de snapshots.

El estado de préstamo no se almacena ni se refresca: la ficha del portal enlaza a `source_url`, la ficha original del OPAC, donde se consulta el estado actual.

## Decisiones

- **Monorepo**: un solo repositorio con `backend/` y `frontend/` simplifica Docker Compose y OpenSpec.
- **PostgreSQL como fuente de verdad**: el índice se puede reconstruir y se conserva el historial.
- **Meilisearch**: ligero, con facetas y typo-tolerance; migrable a OpenSearch si crece el volumen.
- **Snapshots en disco**: permiten reprocesar sin volver a golpear el OPAC.
- **Sin cola distribuida en el MVP**: APScheduler en un único proceso; suficiente para el volumen inicial.
