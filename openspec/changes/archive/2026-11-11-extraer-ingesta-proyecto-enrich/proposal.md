# Proposal

## Why

La ingesta ha crecido hasta ser un sistema de larga duración con su propio ciclo de vida, dependencias y operación, pero sigue mezclada con una API y un portal de solo lectura. Separarla en un proyecto dedicado aísla fallos y despliegues, permite escalar la recolección sin tocar el portal y evita que el proyecto público mantenga código de escritura que ya no ejecuta.

## What Changes

- **BREAKING** Crear el repositorio `mediateca-madrid-enrich`, que asume el descubrimiento, enriquecimiento, indexación, worker/scheduler, migraciones y escritura en PostgreSQL y Meilisearch.
- **BREAKING** Crear el repositorio `mediateca-madrid-shared` con los modelos ORM/Pydantic y los contratos OpenAPI/JSON compartidos; la API y enrich fijan una versión del paquete.
- **BREAKING** `mediateca-madrid` deja de ingerir y de escribir el catálogo: conserva la API y el portal, consume el paquete compartido y trabaja en modo solo lectura.
- La API mantiene su contrato HTTP; el frontend genera tipos TypeScript desde los contratos compartidos.
- PostgreSQL y Meilisearch son compartidos: enrich es dueño del esquema, las migraciones y las escrituras del índice; la API solo lee.
- Cada proyecto mantiene su propio Docker Compose; enrich despliega la infraestructura y la app se conecta por variables de entorno.
- **BREAKING** Los cambios activos de ingesta (`estado-ingesta`, `cola-worker`, `descubrimiento-catalogo`, `enriquecimiento-fichas`, `indexacion-incremental`, `observabilidad-ingesta`) se replanifican en `mediateca-madrid-enrich` y se retiran de este repositorio.
- El código de ingesta, sus tests, fixtures, comandos CLI y servicios de Compose salen de este repositorio.

## Capabilities

### New Capabilities

- `contratos-compartidos`: modelos de dominio, esquemas Pydantic, contratos OpenAPI/JSON y reglas de versionado y compatibilidad entre enrich, API y portal.

### Modified Capabilities

- `ingesta-catalogo`: la recolección y la persistencia pasan a `mediateca-madrid-enrich`; el proyecto actual deja de ejecutar ingesta y de escribir metadatos.
- `operacion-despliegue`: se pasa a dos despliegues separados que comparten PostgreSQL y Meilisearch, con enrich como dueño de migraciones e índice y la app en solo lectura.
- `modelo-catalogo`: el modelo ORM y el esquema dejan de ser locales y pasan a un paquete compartido versionado.

## Impact

- Repositorios: nuevos `mediateca-madrid-enrich` y `mediateca-madrid-shared`; `mediateca-madrid` se reduce a API, portal, contratos de consumo y operación de lectura.
- Código que sale de este repo: `catalog/harvester.py`, `catalog/parser.py`, `catalog/repository.py`, `catalog/jobs.py`, `catalog/soportes.py`, escritura de `catalog/indexer.py`, `cli.py` de ingesta, `core/db.py` de escritura, migraciones de ingesta, fixtures y tests asociados.
- Código que se comparte: modelos SQLAlchemy, esquemas de dominio, `api/schemas.py` como contrato y artefactos OpenAPI/JSON.
- Infraestructura: dos `docker-compose.yml`, red/volúmenes compartidos, variables de conexión, healthchecks, orden de despliegue y rollback.
- CI/CD: publicación versionada del paquete compartido, pipeline de enrich y pipeline de app; compatibilidad entre versiones.
- Documentación: README, arquitectura, Makefiles y guías de operación de los tres repos.
- Riesgo principal: ventana de incompatibilidad entre versiones del modelo o del contrato; se mitiga con versionado y despliegue ordenado (shared → enrich → app).
