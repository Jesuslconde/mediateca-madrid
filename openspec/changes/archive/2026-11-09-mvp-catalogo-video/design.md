# Design

## Context

El OPAC de la Comunidad de Madrid es AbsysNet. No se ha encontrado un endpoint público Z39.50/SRU/OAI: los puertos habituales están cerrados y las rutas SRU/OAI devuelven 404 o HTML de sesión expirada. La única vía disponible hoy es la recolección HTTP de las páginas del OPAC, que usan sesiones efímeras y formularios `ACC`.

El catálogo mezcla DVD y Blu-ray bajo el formato `Videos y DVD`. La información de soporte existe en `MARC 300$a` y en el campo `Soporte` de cada ejemplar.

## Goals / Non-Goals

**Goals:**

- Ingesta reproducible y respetuosa con el OPAC.
- Modelo que separe obra, edición y ejemplar.
- Índice con facetas, incluido `soporte` normalizado.
- API y portal mínimos pero funcionales.
- Despliegue local con Docker Compose.

**Non-Goals:**

- Réplica completa y en tiempo real de todo el catálogo.
- Préstamo, reservas o autenticación de usuarios.
- Sustituir el OPAC oficial.
- Acceso a datos personales.

## Decisions

### Un monorepo con dos imágenes

Se usa un único repositorio con `backend/` y `frontend/`. Es más sencillo para Docker Compose, para compartir especificaciones OpenSpec y para desplegar. Alternativa descartada: varios repositorios, que complican la orquestación y el versionado del contrato API.

### Backend Python

FastAPI + SQLAlchemy 2 + httpx + BeautifulSoup. Python encaja con el scraping y el parseo MARC/HTML; FastAPI da OpenAPI y validación. Alternativa descartada: Node.js para todo, que obligaría a duplicar el stack de ingesta.

### PostgreSQL como fuente de verdad

Los datos normalizados se guardan en PostgreSQL. Meilisearch es un índice derivado y reconstruible. Alternativa descartada: usar solo Meilisearch, que complica la integridad referencial y el historial.

### Meilisearch en lugar de Elasticsearch

Para el MVP, Meilisearch ofrece facetas, filtros y typo-tolerance con menos recursos. Si el volumen o la relevancia lo exigen, se puede migrar a OpenSearch sin cambiar el contrato de la API. Alternativa descartada: Elasticsearch desde el inicio, más pesado para desarrollo local.

### Snapshots en sistema de ficheros

El MVP guarda HTML crudo en un volumen local, no en S3/MinIO. La interfaz `RawStore` permite añadir S3 después. Alternativa descartada: MinIO desde el inicio, que añade un servicio sin beneficio inmediato.

### Soporte a nivel de edición y ejemplar

La edición guarda una lista de soportes detectados; cada ejemplar guarda su soporte concreto. Esto permite packs DVD + Blu-ray y filtros por disponibilidad real. Alternativa descartada: un único campo `soporte` en la edición, que perdería información.

### Sin cola distribuida en el MVP

El scheduler ejecuta tareas en un único proceso con APScheduler. La ingesta y la indexación se pueden lanzar también por CLI. Alternativa descartada: Celery/RabbitMQ, innecesario para el volumen inicial.

## Risks / Trade-offs

- [El HTML del OPAC cambia] → Selectores centralizados en `parser.py` y tests con fixture representativo.
- [Sesión caducada o reCAPTCHA] → Renovación de sesión, backoff y parada controlada; no se intenta eludir el captcha.
- [Datos incompletos o heterogéneos] → Campos opcionales y normalización tolerante; el índice no falla por un campo ausente.
- [Disponibilidad desactualizada] → Se muestra la fecha de actualización y se programa un refresco periódico.
- [Volumen alto] → Ingesta por lotes, paginación y posibilidad de limitar consultas/páginas.
- [Reutilización legal de metadatos] → Solo metadatos públicos, atribución de la fuente y revisión de condiciones antes de publicar.

## Migration Plan

1. Levantar PostgreSQL y Meilisearch con Docker Compose.
2. Ejecutar `mediateca init-db` para crear el esquema.
3. Ejecutar una ingesta de prueba con un límite pequeño.
4. Indexar y verificar `/api/search` y el portal.
5. Programar la ingesta incremental y el refresco de disponibilidad.

Rollback: detener los servicios y restaurar el volumen de PostgreSQL; el índice se reconstruye desde la base de datos.

## Open Questions

Ninguna que bloquee el MVP. La migración a OpenSearch y el almacenamiento S3 quedan para una fase posterior.
