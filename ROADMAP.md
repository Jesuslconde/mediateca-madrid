# Roadmap

## M0 · MVP del catálogo de vídeo

Estado: completado (cambio OpenSpec `mvp-catalogo-video`, archivado el 2026-11-09).

- Ingesta del OPAC con sesión y snapshots.
- Modelo obra / edición / ejemplar.
- Parser y detección de DVD / Blu-ray.
- Índice con facetas.
- API REST.
- Portal con búsqueda y ficha.
- Docker Compose.

## Arquitectura del monorepo

| Ruta | Responsabilidad |
|---|---|
| `services/api` | API FastAPI y lectura de PostgreSQL/Meilisearch |
| `services/enrich` | Ingesta, descubrimiento, enriquecimiento, worker, scheduler, migraciones e índice |
| `apps/web` | Portal Next.js |
| `packages/shared` | Modelos SQLAlchemy, esquemas Pydantic y contratos OpenAPI/JSON |

Imagenes: `mediateca-batch` para la ingesta y `mediateca-web` para API y portal. Orden de despliegue: `db/meilisearch -> init -> batch/web`.

## Planes OpenSpec

En este repositorio solo queda activo `extraer-ingesta-proyecto-enrich`.

La planificación de ingesta se consolido en `openspec/` en la raíz:

| Cambio | Estado |
|---|---|
| `estado-ingesta` | implementado |
| `cola-worker` | implementado |
| `descubrimiento-catalogo` | pendiente |
| `enriquecimiento-fichas` | pendiente |
| `indexacion-incremental` | pendiente |
| `observabilidad-ingesta` | pendiente |

## M1 · Ingesta completa

Se ejecuta en `services/enrich`.

- Descubrir los 67.215 registros de formato 6, incluidos VHS.
- Crear stubs con metadatos básicos.
- Enriquecer todas las fichas en lotes de 5.000.
- Guardar solo datos parseados, sin HTML crudo.
- Indexar de forma incremental.

## M2 · Disponibilidad

Descartado por decisión de producto. El portal no muestra estado de préstamo ni ofrece filtro «Solo disponible». La consulta del préstamo se delega al OPAC oficial mediante el enlace de la ficha.

## M3 · Enriquecimiento externo

Se ejecuta en `services/enrich` y se publica a través de la API.

- Portadas y sinopsis desde TMDb/Filmaffinity/IMDb.
- Enlaces a plataformas legales.
- Valoraciones y datos de reparto adicionales.

## M4 · API pública

- Versionado de API.
- Exportación MARC/JSON.
- Límites de uso y claves.
- Documentación OpenAPI publicada desde `contracts/`.

## M5 · Escala y operación

- Migración a OpenSearch si el volumen lo exige.
- Solo datos parseados: sin almacenamiento de snapshots HTML.
- Cola en PostgreSQL y worker en `services/enrich`; sin Redis/RabbitMQ en el MVP.
- Métricas, cobertura y alertas básicas en enrich.
- Despliegue en producción con backups y orden `init -> batch/web`.
