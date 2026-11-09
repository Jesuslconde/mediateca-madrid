# Tasks

## 1. Preparación y congelación

- [x] 1.1 Congelar cambios de ingesta en este repositorio y etiquetar el estado actual; verificar con `git tag` que existe la etiqueta y que el README indica que la ingesta se moverá a `mediateca-madrid-enrich`.
- [x] 1.2 Inventariar módulos, tests, fixtures, migraciones y servicios de Compose que se mueven; verificar que el inventario cubre todo `backend/src/mediateca/catalog`, `cli.py`, migraciones de ingesta y tests asociados.

## 2. Repositorio compartido

- [x] 2.1 Crear `mediateca-madrid-shared` con `pyproject.toml`, paquete `mediateca_shared`, CI y README; verificar que `python -m build` genera una wheel instalable.
- [x] 2.2 Extraer modelos SQLAlchemy, `Base`, constantes de dominio, esquemas Pydantic y `SCHEMA_VERSION` al paquete compartido; verificar con `pytest` que los modelos y esquemas se importan desde `mediateca_shared`.
- [x] 2.3 Añadir el script de exportación de `openapi.json` y publicarlo como artefacto; verificar que el JSON es válido y contiene las rutas y esquemas esperados.
- [x] 2.4 Añadir `schema_meta` y el helper de comprobación de versión al contrato compartido; verificar con un test que una versión incompatible devuelve error.
- [x] 2.5 Publicar la versión `0.1.0` del paquete; verificar que app y enrich pueden instalarla fijando la versión y que la CI reproduce la instalación.

## 3. Proyecto enrich

- [x] 3.1 Crear `mediateca-madrid-enrich` con paquete `mediateca_enrich`, `pyproject.toml`, Dockerfile y CI; verificar que la imagen se construye y que `ruff` pasa.
- [x] 3.2 Mover `harvester.py`, `parser.py` y `soportes.py` al proyecto enrich y adaptar sus imports; verificar con los tests de parser y soportes que los fixtures siguen funcionando.
- [x] 3.3 Mover `repository.py`, `jobs.py` y el escritor de `indexer.py` a enrich; verificar con tests que la persistencia, los jobs, el worker y la indexación funcionan contra PostgreSQL y Meilisearch.
- [x] 3.4 Mover la CLI existente de ingesta, la configuración de ingesta y la sesión de escritura; verificar que `mediateca --help` en enrich lista `harvest`, `index`, `status`, `worker`, `scheduler` e `init-db`, y que la app ya no tiene CLI de ingesta. `discover` y `enrich` se añadirán en sus cambios migrados.
- [x] 3.5 Mover migraciones SQL, fixtures y tests de ingesta; verificar que `make migrate` es idempotente y que `pytest -q` pasa en enrich.
- [x] 3.6 Añadir el `docker-compose.yml` de enrich con PostgreSQL, Meilisearch, worker, scheduler, volúmenes y red externa `mediateca`; verificar con `docker compose config` y un arranque real.
- [x] 3.7 Ejecutar un ciclo completo con la CLI extraída: `harvest` (descubrimiento y enriquecimiento en una pasada), `index` y procesamiento de un trabajo con el worker; verificar que los datos aparecen en PostgreSQL y en el índice compartido. El descubrimiento masivo y el enriquecimiento por lotes se verifican en sus cambios migrados.
- [x] 3.8 Documentar en el README de enrich el arranque, la migración, la ingesta, el worker y la operación; verificar que los comandos documentados funcionan tal cual.

## 4. App en solo lectura

- [x] 4.1 Fijar `mediateca-shared` en la app y eliminar las copias locales de modelos y esquemas que ahora vienen del paquete; verificar con `pytest` que la API arranca con los imports compartidos.
- [x] 4.2 Eliminar el código de ingesta, los comandos CLI de ingesta, los tests, fixtures, migraciones y el servicio `raw_data` de la app; verificar con `rg` que no quedan referencias a harvester, parser, worker, scheduler ni snapshots en el backend.
- [x] 4.3 Sustituir el indexador por un adaptador de búsqueda de solo lectura y retirar `ensure_index` e `index_editions` del arranque de la app; verificar con tests de búsqueda y una petición de humo a `/api/search`.
- [x] 4.4 Añadir la comprobación de `schema_version` al arrancar la API; verificar que falla con un error legible si el esquema falta o es incompatible y que arranca si coincide.
- [x] 4.5 Generar los tipos TypeScript del portal desde el `openapi.json` compartido y sustituir los tipos manuales; verificar con `npm run build` y un test de compatibilidad del contrato.
- [x] 4.6 Retirar de `docker-compose.yml` los servicios de ingesta y las variables exclusivas de ingesta, y conectar la app a la red externa compartida; verificar con `docker compose config` y un arranque contra enrich.
- [x] 4.7 Actualizar README, Makefile y `docs/ARCHITECTURE.md` de la app para reflejar el modo solo lectura y los tres repositorios; verificar que los comandos documentados funcionan y que no mencionan ingesta local.

## 5. Replanificación de OpenSpec

- [x] 5.1 Copiar los cambios `estado-ingesta`, `cola-worker`, `descubrimiento-catalogo`, `enriquecimiento-fichas`, `indexacion-incremental` y `observabilidad-ingesta` al OpenSpec de enrich; verificar con `openspec list --json` que aparecen los seis.
- [x] 5.2 Copiar a enrich las especificaciones de ingesta ya implementadas y configurar su contexto OpenSpec; verificar con `openspec validate --all` que no hay errores.
- [x] 5.3 Archivar o marcar como supersedidos esos seis cambios en este repositorio, dejando la ruta al nuevo proyecto; verificar con `openspec list --json` que no quedan cambios activos de ingesta aquí.

## 6. Integración y corte

- [x] 6.1 Ensayar el despliegue ordenado shared → enrich → app en un entorno de staging; verificar que el portal lee datos y que una ingesta actualiza el índice.
- [x] 6.2 Documentar y probar el rollback a la versión anterior de la app sin deshacer migraciones; verificar que el portal vuelve a funcionar con la etiqueta anterior.
- [x] 6.3 Ejecutar la verificación posterior al corte: healthchecks de app y worker, `/api/search`, `/api/records/{titn}`, `mediateca status` en enrich y cobertura de datos.
- [x] 6.4 Actualizar `ROADMAP.md` y la documentación raíz con la nueva arquitectura y los enlaces a los tres repositorios; verificar que no quedan referencias a un despliegue único con ingesta.

## Workflow follow-up

- Archivar este cambio cuando la extracción y el corte estén completos.
- Verificar las especificaciones archivadas en este repositorio y en el nuevo proyecto.
