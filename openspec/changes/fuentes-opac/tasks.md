# Tasks

## 1. Modelo compartido y migración

- [ ] 1.1 Añadir el modelo `Fuente` en `packages/shared` con código único, nombre, adaptador, perfil OPAC, estado, retardo y política de captcha; verificar con una prueba que el código se valida contra `^[a-z0-9][a-z0-9-]*$` y que no admite duplicados.
- [ ] 1.2 Añadir `fuente_id` y `record_id` a `Edicion`, `fuente_id` a `Biblioteca`, `Sucursal`, `Ejemplar` y `HarvestJob`, y `record_id` a `ListaItem`; verificar con las pruebas de esquema de `packages/shared` que las relaciones y las unicidades compuestas se crean.
- [ ] 1.3 Implementar la composición y el parseo de `record_id` (`<fuente>:<titn>`) con resolución de un `TITN` suelto a Madrid; verificar los casos válido, fuente desconocida y formato inválido con pruebas unitarias.
- [ ] 1.4 Crear `services/enrich/scripts/migrate_fuentes.sql` idempotente: tabla `fuentes`, siembra de Madrid, columnas de fuente, `record_id`, migración de `lista_items`, nuevas unicidades y `SCHEMA_VERSION=7`; verificar ejecutándola dos veces sobre una base de prueba sin errores ni duplicados.
- [ ] 1.5 Ajustar `upsert_edicion`, `upsert_stub`, `get_or_create_biblioteca`, `_sync_ejemplares` y `upsert_sucursal` para operar por `(fuente, titn)` y `(fuente, codigo)`; verificar con pruebas que el mismo `TITN` o código en dos fuentes no se reutiliza.
- [ ] 1.6 Ajustar `mark_absent_since`, `select_pending_titns`, `count_pending_titns` y `record_enrich_failure` para filtrar por fuente; verificar que un descubrimiento de Madrid no marca ausentes ediciones de otra fuente.
- [ ] 1.7 Actualizar las pruebas de modelo y repositorio para cubrir la migración de Madrid a `record_id` y la unicidad de `external_key` por fuente; verificar con `make test-shared` y `make test-enrich`.

## 2. Fuente, cliente OPAC y recolección

- [ ] 2.1 Cargar la fuente desde la base y sembrar Madrid desde `MEDIATECA_OPAC_BASE_URL` y `MEDIATECA_OPAC_PATH` cuando no exista; verificar que una fuente deshabilitada no se ofrece a la ingesta.
- [ ] 2.2 Refactorizar `OpacClient` para recibir el perfil de la fuente y usar su URL, ruta, patrón de sesión, filtro de formato, retardo y contadores propios; verificar con una prueba que dos perfiles con rutas distintas abren sesiones separadas.
- [ ] 2.3 Añadir fixtures de prueba del listado y la ficha de AbsysNet, incluido un perfil con patrón `abnetcl.cgi`, y verificar que el parser obtiene `TITN`, título, descripción física y ejemplares sin depender de la ruta de Madrid.
- [ ] 2.4 Pasar la fuente al `Harvester` y a las funciones de repositorio; verificar que un enriquecimiento de Madrid no selecciona pendientes de otra fuente.
- [ ] 2.5 Ajustar los contadores de captcha, sesión y renovaciones para que sean por fuente; verificar que resolver un captcha en una fuente no altera los contadores de otra.
- [ ] 2.6 Actualizar los comandos de recolección de la CLI con `--fuente` (Madrid por defecto) y verificar `harvest`, `discover` y `enrich` contra una fuente de prueba.

## 3. Trabajos, scheduler y worker

- [ ] 3.1 Añadir `fuente_id` a `HarvestJob` y a `create_job`/`enqueue_*`; verificar que un trabajo de descubrimiento, enriquecimiento, TMDB o branches conserva su fuente y que el indexado global puede quedar sin fuente.
- [ ] 3.2 Calcular deduplicación y bloqueos por fuente, con el indexado global bloqueando todas; verificar con pruebas que dos `enrich` de fuentes distintas conviven y dos del mismo tipo y fuente no.
- [ ] 3.3 Hacer que el scheduler recorra solo fuentes habilitadas y evalúe intervalos, último trabajo y pendientes por fuente; verificar que una fuente deshabilitada no recibe trabajos y que las demás siguen su programación.
- [ ] 3.4 Ajustar el reclamo atómico y el heartbeat para trabajos con fuente; verificar con dos workers que no se reclama dos veces el mismo trabajo y que un indexado global impide reclamar ingestas.
- [ ] 3.5 Ajustar las estadísticas de trabajos y la cobertura para incluir la fuente y el desglose por fuente; verificar con `make test-enrich` y una consulta de estado con dos fuentes de prueba.
- [ ] 3.6 Añadir `fuente` a los logs estructurados y a las métricas de ingesta; verificar que dos registros con el mismo `TITN` en fuentes distintas se distinguen en logs y contadores.

## 4. Índice y búsqueda

- [ ] 4.1 Cambiar el documento de índice para usar `id = record_id` y añadir `record_id`, `fuente` y `fuente_nombre`; verificar que dos ediciones con el mismo `TITN` producen dos documentos distintos.
- [ ] 4.2 Prefijar `ubicaciones` con la fuente (`b:<fuente>:<codigo>`, `s:<fuente>:<codigo>`) y añadir `fuente` a facetas y atributos filtrables; verificar con `make test-enrich` y una búsqueda con dos fuentes de prueba.
- [ ] 4.3 Añadir el filtro `fuente` y normalizar códigos de ubicación históricos sin fuente a Madrid; verificar que `b:RBMALC` y `b:madrid:RBMALC` devuelven el mismo resultado.
- [ ] 4.4 Ajustar el indexado incremental para que reciba la fuente del lote y el indexado completo para recorrer todas las fuentes; verificar que un lote de una fuente no reindexa documentos de otra.
- [ ] 4.5 Actualizar las pruebas del indexador y la documentación de `make index`/reindexado; verificar con `make test-enrich` y `make lint`.

## 5. API y contrato

- [ ] 5.1 Implementar la resolución de `record_id` en la API y la compatibilidad con `TITN` suelto; verificar `/api/records/madrid:2101557`, `/api/records/2101557` y un identificador inválido.
- [ ] 5.2 Añadir `record_id`, `fuente` y `fuente_nombre` a la ficha y construir `source_url` con el perfil de la fuente; verificar que una edición de prueba no usa la URL de Madrid.
- [ ] 5.3 Añadir el filtro `fuente` a `/api/search` y devolver la fuente y el `record_id` en los resultados; verificar que el filtro se combina con texto y soporte.
- [ ] 5.4 Añadir la fuente a `/api/locations` y a los códigos `b:`/`s:`; verificar que el mismo código en dos fuentes devuelve dos ubicaciones distintas.
- [ ] 5.5 Migrar las rutas y la respuesta de listas a `record_id`, manteniendo la compatibilidad con `TITN` suelto; verificar crear, consultar, añadir y quitar con ambos formatos.
- [ ] 5.6 Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts`, y actualizar las pruebas de contrato; verificar con `make openapi`, `make web-types` y `make check-schema`.

## 6. Portal web

- [ ] 6.1 Renombrar la ruta de ficha a `app/registro/[recordId]` y adaptar la llamada a la API para aceptar `record_id` y `TITN` suelto; verificar `/registro/2101557` y `/registro/madrid:2101557`.
- [ ] 6.2 Usar `record_id` en los enlaces de resultados, fichas, listas y navegación interna; verificar que una búsqueda y una lista generan enlaces con `record_id` y que los antiguos siguen abriendo la ficha.
- [ ] 6.3 Mostrar la etiqueta de la fuente en la ficha sin selector de comunidad; verificar que una edición de Madrid muestra su fuente y que una fuente desconocida se identifica por código.
- [ ] 6.4 Añadir la fuente a los tipos del cliente y al selector de ubicaciones si el contrato la expone; verificar que la compilación del portal no falla con los tipos regenerados.
- [ ] 6.5 Actualizar los textos y la documentación del portal sobre las URLs de ficha; verificar con `npm run lint` y `npm run build` en `apps/web`.

## 7. Directorio de bibliotecas

- [ ] 7.1 Pasar la fuente a `DirectoryClient`, `refresh_sucursales`, `update_biblioteca_location` y `upsert_sucursal`; verificar que una ficha de Madrid no actualiza una biblioteca de otra fuente con el mismo código.
- [ ] 7.2 Añadir `--fuente` a `refresh-branches` y `enqueue-branches`; verificar que una fuente sin directorio informa de la ausencia sin fallar y no modifica datos.
- [ ] 7.3 Actualizar las pruebas del directorio para cubrir el emparejamiento por fuente y la idempotencia; verificar con `make test-enrich`.

## 8. Operación, documentación y verificación final

- [ ] 8.1 Ajustar `init` para detectar el salto de `SCHEMA_VERSION` a `7` y ejecutar `index --reset` solo en ese caso; verificar en un entorno de prueba que el índice no conserva identificadores antiguos.
- [ ] 8.2 Actualizar `README.md`, `.env.example` y la documentación de despliegue con la fuente, la migración, el reindexado y el rollback; verificar que los comandos documentados se ejecutan tal cual.
- [ ] 8.3 Ejecutar la verificación integrada: `make test`, `make lint`, `make openapi`, `make web-types` y `make check-schema`; verificar que no hay fallos.
- [ ] 8.4 Hacer una prueba de humo con Madrid: búsqueda, ficha por `record_id`, ficha por `TITN` antiguo, listas históricas y selector de ubicaciones; verificar que los resultados coinciden con el comportamiento anterior.
- [ ] 8.5 Revisar que una fuente deshabilitada o sin datos no altera la cobertura, la búsqueda ni el scheduler; verificar con una fuente de prueba deshabilitada.

## Workflow follow-up

- Archivar el cambio después de que la revisión del proyecto esté satisfecha.
- Verificar el resultado archivado y que las especificaciones principales reflejan la identidad por fuente.
