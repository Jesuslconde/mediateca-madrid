# Design

## Context

Ver `proposal.md` para la motivación. Estado actual relevante:

- Un único repositorio con backend Python (`mediateca`) y frontend Next.js.
- El backend mezcla lectura (API) y escritura (harvester, parser, repositorio, worker, scheduler, indexador).
- `catalog/models.py` es local y `api/schemas.py` define el contrato HTTP.
- PostgreSQL y Meilisearch se despliegan en el `docker-compose.yml` de este repositorio.
- Los cambios `estado-ingesta` y `cola-worker` ya están implementados aquí; `descubrimiento-catalogo`, `enriquecimiento-fichas`, `indexacion-incremental` y `observabilidad-ingesta` están planificados.
- No hay registro de paquetes privado ni monorepo de workspaces.

## Goals / Non-Goals

**Goals:**

- Extraer la ingesta a `mediateca-madrid-enrich` sin cambiar el contrato HTTP del portal.
- Publicar modelos y contratos desde `mediateca-madrid-shared` con versionado semántico.
- Dejar la app en modo solo lectura, sin esquema, sin worker y sin servicios de ingesta.
- Mantener PostgreSQL y Meilisearch compartidos, con enrich como único escritor.
- Replanificar los cambios de ingesta en el nuevo repositorio sin perder su contenido.

**Non-Goals:**

- Cambiar la experiencia de búsqueda o las rutas de la API.
- Añadir un framework de migraciones (Alembic) en esta extracción.
- Introducir un monorepo de workspaces o un único despliegue conjunto.
- Decidir aquí si se eliminan los snapshots HTML; eso corresponde a `enriquecimiento-fichas`.

## Decisions

### 1. Tres repositorios independientes

- `mediateca-madrid`: API FastAPI, portal Next.js y operación de lectura.
- `mediateca-madrid-enrich`: ingesta, worker, scheduler, migraciones e índice.
- `mediateca-madrid-shared`: paquete Python `mediateca_shared` con modelos, esquemas y contratos.

**Por qué**: separa ciclos de vida y fallos; el paquete compartido evita duplicar el modelo.  
**Alternativa descartada**: monorepo con workspaces. Mantendría acoplados los despliegues y no era lo pedido.

### 2. Paquete compartido como wheel versionada

`mediateca-madrid-shared` publica una wheel con versionado semántico. App y enrich fijan `mediateca-shared==X.Y.Z` en su `pyproject.toml`. Si no hay registro privado disponible, se instala desde un tag de Git fijado por commit.

**Por qué**: una fuente única de modelos y contratos, con actualizaciones explícitas.  
**Alternativa descartada**: submódulo Git o copia de modelos. Dificulta la compatibilidad y la trazabilidad.

### 3. Contenido del paquete compartido

Se mueven a `mediateca_shared`:

- Modelos SQLAlchemy y `Base`.
- Esquemas Pydantic de dominio y de respuesta de la API.
- Constantes de dominio: tipos de soporte, estados de trabajo y tipos de trabajo.
- `SCHEMA_VERSION` y helpers de validación de versión.
- El contrato `openapi.json` publicado como artefacto de release.

No se mueven: routers, serializers de proyección, clientes HTTP, configuración de entorno ni sesiones de base de datos. Cada proyecto configura su motor y su sesión.

**Por qué**: el paquete describe el dominio y el contrato, no la infraestructura de cada servicio.

### 4. Migraciones y versión de esquema

Enrich conserva las migraciones SQL idempotentes y es el único que las ejecuta. Se añade una tabla `schema_meta` con `schema_version`; la migración la actualiza y la app la compara con `SCHEMA_VERSION` al arrancar.

**Por qué**: la app necesita detectar un esquema incompatible sin ejecutar DDL.  
**Alternativa descartada**: confiar solo en la versión del paquete Python. No detecta una migración pendiente en la base.

### 5. App en solo lectura

- `api/main.py` deja de llamar a `init_db()` para crear tablas; solo verifica conexión y versión.
- Se elimina `raw_data` y los servicios `worker`/`scheduler` del compose de la app.
- El índice pasa a un adaptador de búsqueda de solo lectura; no hay `ensure_index` ni `index_editions` en la app.
- Los handlers de ingesta y los comandos `harvest`, `discover`, `enrich`, `index`, `worker` y `scheduler` salen de la CLI de la app.

**Por qué**: elimina escrituras accidentales y dependencias de OPAC en el servicio público.

### 6. Infraestructura compartida

`mediateca-madrid-enrich` despliega PostgreSQL, Meilisearch, worker y scheduler. Crea una red Docker externa `mediateca` y publica los puertos de PostgreSQL y Meilisearch. La app declara esa red como externa y se conecta por `MEDIATECA_DATABASE_URL` y `MEDIATECA_MEILISEARCH_URL`.

**Por qué**: los compose siguen siendo independientes pero comparten almacenamiento.  
**Alternativa descartada**: base propia con ETL. Añade latencia y duplicación sin necesidad.

### 7. Contrato OpenAPI y tipos del portal

La app genera `openapi.json` en CI a partir de los esquemas compartidos y lo publica como artefacto de release en `mediateca-madrid-shared`. El portal genera tipos TypeScript con `openapi-typescript` desde ese artefacto fijado. La CI falla si el contrato y los tipos no coinciden.

**Por qué**: el contrato sigue siendo el de la API, pero se versiona y consume desde un único sitio.  
**Alternativa descartada**: tipos manuales en el portal. Se desincronizan con facilidad.

### 8. Replanificación de los cambios activos

Los seis cambios de ingesta se copian a `openspec/changes/` del nuevo repositorio antes de retirarlos aquí:

- `estado-ingesta` y `cola-worker` pasan como base ya implementada.
- `descubrimiento-catalogo`, `enriquecimiento-fichas`, `indexacion-incremental` y `observabilidad-ingesta` pasan como planificación pendiente.
- En este repositorio se archivan como supersedidos, dejando una nota con la ruta al nuevo proyecto.

**Por qué**: evita dos planificaciones divergentes y conserva el trabajo hecho.

## Risks / Trade-offs

- [Desfase de versiones entre shared, enrich y app] → `schema_meta`, comprobación al arrancar y orden shared → enrich → app.
- [Doble código durante la transición] → congelar la ingesta en la app y retirarla en el mismo release que activa enrich.
- [Complejidad de dos compose y red externa] → red `mediateca` documentada y `.env.example` con URLs explícitas.
- [La app lee un índice que enrich aún no ha actualizado] → indexación al final del lote y tolerancia a resultados eventuales.
- [Deriva del contrato OpenAPI] → artefacto generado, versión fijada y comprobación en CI.
- [Pérdida de historial de los cambios activos] → copiarlos al nuevo OpenSpec antes de archivarlos aquí.
- [Migración destructiva antes de validar] → mantener el esquema compatible durante la ventana de corte y posponer cambios destructivos.

## Migration Plan

1. **Congelación**: no añadir funcionalidad de ingesta nueva en este repositorio.
2. **Shared**: crear el repositorio, extraer modelos/esquemas/constantes, publicar `0.1.0` y el contrato OpenAPI.
3. **Enrich**: crear el repositorio, mover harvester, parser, repositorio de escritura, worker, scheduler, indexador de escritura, migraciones, fixtures y tests; fijar shared; validar contra PostgreSQL y Meilisearch.
4. **App**: fijar shared, eliminar código/servicios de ingesta, adaptar la búsqueda a solo lectura y añadir la comprobación de `schema_version`.
5. **Cambios**: copiar los seis cambios de ingesta al OpenSpec de enrich y archivarlos aquí como supersedidos.
6. **Corte**: detener la ingesta en la app, arrancar enrich, verificar que el portal sigue leyendo y que la ingesta actualiza el índice.
7. **Rollback**: mantener etiquetada la versión anterior de la app y su compose con ingesta; si falla el corte, volver a esa versión sin ejecutar migraciones destructivas.

## Open Questions

- Registro definitivo para publicar la wheel (GitHub Packages, PyPI privado o instalación desde tag de Git). No cambia el diseño ni las tareas, solo el comando de publicación.
- Si `enriquecimiento-fichas` elimina finalmente los snapshots HTML, la extracción moverá primero el código actual y ese cambio decidirá la retirada.
