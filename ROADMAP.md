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

## Arquitectura de repositorios

| Repositorio | Responsabilidad |
|---|---|
| `mediateca-madrid` | API FastAPI y portal Next.js; PostgreSQL y Meilisearch en solo lectura |
| `mediateca-madrid-enrich` | Ingesta, descubrimiento, enriquecimiento, worker, scheduler, migraciones e índice |
| `mediateca-madrid-shared` | Modelos SQLAlchemy, esquemas Pydantic y contratos OpenAPI/JSON |

Orden de despliegue: shared → enrich (migraciones) → app.

## Planes OpenSpec

En este repositorio solo queda activo `extraer-ingesta-proyecto-enrich`.

La planificación de ingesta se trasladó a `mediateca-madrid-enrich`:

| Cambio | Estado |
|---|---|
| `estado-ingesta` | implementado en enrich |
| `cola-worker` | implementado en enrich |
| `descubrimiento-catalogo` | pendiente en enrich |
| `enriquecimiento-fichas` | pendiente en enrich |
| `indexacion-incremental` | pendiente en enrich |
| `observabilidad-ingesta` | pendiente en enrich |

## M1 · Ingesta completa

Se ejecuta en `mediateca-madrid-enrich`.

- Descubrir los 67.215 registros de formato 6, incluidos VHS.
- Crear stubs con metadatos básicos.
- Enriquecer todas las fichas en lotes de 5.000.
- Guardar solo datos parseados, sin HTML crudo.
- Indexar de forma incremental.

## M2 · Disponibilidad

Descartado por decisión de producto. El portal no muestra estado de préstamo ni ofrece filtro «Solo disponible». La consulta del préstamo se delega al OPAC oficial mediante el enlace de la ficha.

## M3 · Enriquecimiento externo

Se ejecuta en `mediateca-madrid-enrich` y se publica a través de la API.

- Portadas y sinopsis desde TMDb/Filmaffinity/IMDb.
- Enlaces a plataformas legales.
- Valoraciones y datos de reparto adicionales.

## M4 · API pública

- Versionado de API.
- Exportación MARC/JSON.
- Límites de uso y claves.
- Documentación OpenAPI publicada desde `mediateca-madrid-shared`.

## M5 · Escala y operación

- Migración a OpenSearch si el volumen lo exige.
- Solo datos parseados: sin almacenamiento de snapshots HTML.
- Cola en PostgreSQL y worker en `mediateca-madrid-enrich`; sin Redis/RabbitMQ en el MVP.
- Métricas, cobertura y alertas básicas en enrich.
- Despliegue en producción con backups y orden shared → enrich → app.
