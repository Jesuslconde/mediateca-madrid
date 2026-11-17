# Arquitectura de la ingesta

## Descubrimiento del catalogo

El descubrimiento enumera el catalogo de video del OPAC sin descargar las fichas de
detalle. Usa la consulta de truncamiento `*` con el filtro de formato `6`
(`Videos y DVD`) y `subcat=/`, de modo que incluye DVD, Blu-ray, 4K UHD y VHS.

La consulta se envia al formulario avanzado (`ACC=131`) con `xsqf01=*` y
`select03=6`. El OPAC devuelve los registros en orden `TITN` ascendente.

## Paginacion profunda

Cada pagina de resultados enlaza la siguiente mediante `ACC=161&DOC=N`. El cliente
recorre esos enlaces hasta que no hay pagina siguiente o se alcanza el limite
solicitado. El parametro `N` es la posicion del primer registro de la pagina y se
usa como cursor de reanudacion.

## Parser de listados

`parse_search_results` recorre los `li.c-docs_unit` de cada pagina y extrae el MARC
oculto (`span.js-*`): `TITN`, `T245`, `T260`, `FEPU`, `LENG`, `T300a`, `T655`,
`MATE` y, cuando existen, autores y notas. Con esos datos crea un `ParsedEdicion`
con metadatos basicos y el soporte detectado desde `T300a`.

## Checkpoint y reanudacion

El trabajo `discover` guarda en `harvest_jobs` el ultimo `DOC` y el ultimo `TITN`
procesados (`cursor_doc` y `cursor_titn`). Al reanudar se repite la busqueda `*` y
se salta al `DOC` guardado. El primer `TITN` leido se compara con el cursor para
detectar cambios del catalogo; si no coincide se registra una advertencia y se
continua desde el punto disponible.

## Sesion caducada

La sesion del OPAC caduca a los pocos minutos. Si ocurre durante la paginacion, el
cliente reabre sesion, repite la busqueda `*` y solicita la pagina `ACC=161&DOC=N`
del punto actual. No se reintenta la URL antigua, porque depende del contexto de
busqueda de la sesion anterior.

## Stubs, altas y bajas

Cada `TITN` descubierto se guarda como edicion stub (`is_stub=true`) con
`discovery_seen_at` y los metadatos basicos del listado. El upsert no sobrescribe
una edicion ya enriquecida: solo actualiza su fecha de ultima visualizacion.

En un descubrimiento completo, las ediciones con `discovery_seen_at` anterior al
inicio del trabajo que no han vuelto a aparecer se marcan con `missing_at`; nunca
se eliminan automaticamente. Las ediciones nuevas quedan pendientes de
enriquecimiento.

## Enriquecimiento por lotes

El enriquecimiento selecciona hasta 5.000 ediciones con `detail_fetched_at` vacio,
ordenadas por `TITN`, descarga la ficha de cada una mediante `?TITN=...&FORM=1`,
la parsea y actualiza la edicion y sus ejemplares. El lote termina cuando no quedan
`TITN` pendientes o se alcanza el limite.

A 1 peticion por segundo, un lote de 5.000 fichas tarda aproximadamente 1,4 horas;
la primera pasada completa de 67.215 fichas requiere unas 14 ejecuciones nocturnas.
El tamano del lote y el retardo son configurables desde `mediateca enrich`.

Cuando un lote termina con pendientes restantes, el worker encadena el siguiente
lote para drenar el backlog (ver "Programacion de la ingesta").

## Campos de enriquecimiento TMDB

La edicion conserva `pais` con el codigo del MARC del OPAC y añade
`paises_origen` con la lista de codigos ISO 3166-1 alfa-2 obtenida de TMDB,
`tmdb_id`, `tmdb_poster_url` (portada de `image.tmdb.org`) y `tmdb_url` (ficha
publica de TMDB). La migracion `scripts/migrate_tmdb.sql` crea las columnas de
forma idempotente, indexa `tmdb_enriched_at` y actualiza
`schema_meta.schema_version` a `3`.

## Estado de enriquecimiento por edicion

Cada edicion conserva el resultado del ultimo intento de enriquecimiento para
distinguir "nunca intentado", "fallo" y "TMDB sin coincidencia". La migracion
`scripts/migrate_enriquecimiento_estado.sql` añade de forma idempotente:

- `enrich_status` (`pending`, `enriched`, `failed`), `enrich_attempts`,
  `enrich_last_attempt_at` y `enrich_last_error` para el enriquecimiento OPAC.
- `tmdb_status` (`pending`, `matched`, `unmatched`, `error`, `skipped`),
  `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error` para TMDB.

El exito de una ficha marca `enrich_status='enriched'` e incrementa
`enrich_attempts`; un fallo terminal marca `'failed'` y guarda el error. TMDB
marca `matched`, `unmatched`, `error` o `skipped` (sin token) e incrementa
`tmdb_attempts` salvo en `skipped`. `tmdb_enriched_at` sigue registrando solo la
ultima coincidencia. La migracion rellena `enrich_status='enriched'` donde ya
habia `detail_fetched_at` y `tmdb_status='matched'` donde ya habia
`tmdb_enriched_at`, sube `SCHEMA_VERSION` a `4` y crea indices por estado.

## Consulta a TMDB

Cuando existe un token efectivo (guardado en `app_config` o en
`MEDIATECA_TMDB_API_TOKEN`), el enriquecimiento consulta `/3/search/movie` con el
titulo y el ano de la edicion y, si hay una coincidencia fiable, `/3/movie/{id}`
para leer `production_countries` con respaldo de `origin_country`, la portada
(`poster_path`) y construir la URL de la imagen y el enlace a TMDB. El token puede
ser una API Key v3, enviada como `api_key`, o un Read Access Token v4, enviado
como `Authorization: Bearer`; el formato se detecta por la forma del token.

El emparejamiento normaliza titulos: elimina la puntuacion final, los
calificadores de forma entre parentesis (`Película cinematográfica`, etc.) y la
mencion de responsabilidad antes de consultar TMDB. Exige un ano dentro de +-1 y
una similitud de al menos 0,90, o coincidencia exacta si la edicion no tiene ano.
Los paises se normalizan a codigos ISO 3166-1 alfa-2 en mayusculas y se
deduplican. El cliente aplica el retardo configurado, respeta `Retry-After` y
reintenta errores temporales con backoff. El token nunca se registra en logs.

## Actualizacion manual de metadatos TMDB

Ademas del enriquecimiento del OPAC, la cola admite un trabajo de tipo `tmdb`
que solo consulta TMDB y actualiza `paises_origen`, `tmdb_id`,
`tmdb_poster_url`, `tmdb_url` y `tmdb_enriched_at`. Se lanza unicamente a mano
desde `Tareas` (`/tareas`) o con `mediateca tmdb-enrich`; el scheduler nunca lo
encola. Por defecto selecciona las ediciones pendientes (sin `tmdb_enriched_at`
o con `tmdb_id` sin `tmdb_url`). Con el modo refresco vuelve a consultar tambien
las ya sincronizadas, ordenadas por `tmdb_enriched_at` mas antiguo y luego por
`TITN`, para rotar los lotes. Al terminar indexa los `TITN` procesados con
`index_titns`.

## Actualizacion manual de direcciones de bibliotecas

La cola admite un trabajo de tipo `branches` que recorre el Directorio de
Bibliotecas de la Comunidad de Madrid y actualiza direccion, codigo postal y
coordenadas de las sucursales. Se lanza unicamente a mano desde `Tareas`
(`/tareas`), con `mediateca enqueue-branches` o `make branches-enqueue`; el
scheduler nunca lo encola. La tarea precarga los codigos de `Biblioteca`
existentes, omite las fichas de bibliotecas desconocidas y crea o actualiza las
sucursales de las bibliotecas conocidas; nunca crea bibliotecas nuevas. El
comando directo `refresh-branches` conserva el comportamiento completo anterior.

## Concurrencia del worker

El worker arranca hasta `MEDIATECA_WORKER_CONCURRENCY` hilos, con un maximo de
cinco (uno por tipo de trabajo). El dashboard guarda el valor en `app_config` y
prevalece sobre el entorno; se aplica al reiniciar el worker. El comando
`mediateca worker --concurrency N` permite una sobreescritura puntual.

Cada hilo reclama trabajos de forma atomica con `FOR UPDATE SKIP LOCKED`. En
PostgreSQL el reclamo se serializa con `pg_advisory_xact_lock`, de modo que dos
hilos o contenedores no pueden reclamar a la vez trabajos incompatibles. El lock
solo cubre el reclamo; la ejecucion sigue siendo paralela.

No se permite el mismo tipo dos veces ni las parejas con dependencia:
`discover`/`enrich`, `enrich`/`tmdb`, `enrich`/`index` y `tmdb`/`index`.
`branches` puede convivir con cualquier trabajo. Un trabajo incompatible se queda
en `pending` y se ejecuta cuando termina el que lo bloquea.

## Cursor, reintentos y errores

El trabajo `enrich` guarda el ultimo `TITN` procesado en `cursor_titn` y actualiza
las estadisticas tras cada ficha. Si el worker se reinicia, el siguiente trabajo
continua desde el siguiente `TITN` pendiente y no repite las fichas ya marcadas con
`detail_fetched_at`.

Cada ficha se reintenta hasta el maximo configurado en el cliente del OPAC. Un fallo
persistente se registra en las estadisticas del trabajo y del `harvest_run`, se
excluye del lote activo y no bloquea al resto. La actualizacion es idempotente por
`TITN`; los ejemplares se sincronizan por `external_key` sin duplicarse.

## Sin snapshots

El enriquecimiento solo persiste datos normalizados en PostgreSQL. No escribe HTML
crudo ni crea archivos en `MEDIATECA_RAW_DIR`. La tabla `snapshots`, el modelo
`Snapshot`, la relacion `Edicion.snapshots` y `save_snapshot` se han retirado;
`scripts/migrate_ingesta.sql` elimina la tabla de forma idempotente.

## Indexacion incremental

Cada lote de descubrimiento o enriquecimiento indexa solo los `TITN` procesados
mediante `index_titns`, sin reconstruir el indice completo. Los `TITN` se consultan
y envian a Meilisearch en lotes de 200; los documentos no mencionados permanecen
intactos.

Cada documento incluye `detail_complete` e `is_stub`. Una edicion descubierta pero
sin `detail_fetched_at` se indexa como stub con `detail_complete=false`; al
enriquecerse se actualiza con `detail_complete=true` y los nuevos campos. Ambos
campos son filtrables. La API publica del portal aplica siempre
`detail_complete = true`, de modo que la web solo muestra fichas enriquecidas.

`paises_origen` se incluye en cada documento como lista (vacia si no hay TMDB),
es filtrable y se devuelve como faceta. Los TITN procesados por un lote se
indexan de forma incremental; tras un cambio de esquema o al anadir el campo a un
indice existente se ejecuta `mediateca index --reset` para reconstruirlo.

Cada documento conserva `bibliotecas` con los nombres de las redes y anade
`ubicaciones` (codigos `b:<biblioteca>` y `s:<sucursal>`) y `ubicaciones_texto`
(nombres visibles). Ambos campos nuevos son filtrables: el portal usa el codigo
estable para el selector agrupado y acepta el nombre como respaldo. Tras
desplegar este cambio hay que ejecutar `make index` para poblar los campos en los
documentos existentes.

Si un lote falla antes de terminar, el worker indexa igualmente los `TITN` que ya
habia procesado. Ademas, el scheduler encola una reindexacion de reconciliacion
cada `index_interval_hours` (168 por defecto) para reparar cualquier divergencia
entre PostgreSQL y Meilisearch.

Si Meilisearch falla al terminar un lote, los `TITN` pendientes se guardan en
`harvest_jobs.stats.pending_index_titns`. El reintento del trabajo los indexa antes
de continuar con el siguiente lote. La reindexacion completa con
`index_editions(reset=True)` queda reservada al comando manual
`mediateca index --reset`, para cambios de esquema o reparaciones.

## Resolucion de captchas con FlareSolverr

La resolucion de captchas es opcional y esta desactivada por defecto. El cliente
del OPAC usa `httpx` como transporte normal y solo invoca a FlareSolverr cuando
detecta la pagina de reCAPTCHA y existe una URL efectiva configurada. La URL se
resuelve al crear cada cliente del OPAC y puede venir de la tabla `app_config`
(configuracion del dashboard) o de `MEDIATECA_FLARESOLVERR_URL`.

La configuracion persistida se guarda en `app_config`:

- `key`: nombre del ajuste, por ejemplo `flaresolverr_url`.
- `value`: valor en texto.
- `updated_at`: fecha de la ultima actualizacion.

`MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS` controla el campo `maxTimeout` de la API de
FlareSolverr, en milisegundos. Por defecto es `60000`.

El cliente usa la API v1 de FlareSolverr mediante `POST {url}/v1` con
`cmd=request.get` o `cmd=request.post`. Para POST envia el formulario en `postData`
codificado como `application/x-www-form-urlencoded`; para GET incorpora los
parametros a la URL. Una respuesta valida tiene `status=ok` y
`solution.response`; de ella se usan el estado HTTP, la URL final, el HTML, las
cookies y el `userAgent`. Se asume una version de FlareSolverr con esta API v1.

FlareSolverr se invoca solo cuando la pagina del OPAC contiene el reCAPTCHA. Si no
hay URL, el servicio no responde o la respuesta sigue siendo un captcha, el
recolector registra el fallo y el trabajo se reprograma con el backoff existente,
sin reintentar la resolucion dentro de la misma peticion.

## Programacion de la ingesta

El servicio `scheduler` solo escribe en `harvest_jobs`; no descarga fichas ni
toca Meilisearch. Cada `MEDIATECA_SCHEDULER_POLL_SECONDS` lee la configuracion de
`app_config` y comprueba si toca encolar:

- `discover` incremental cada `discover_interval_hours` (12 por defecto);
- `discover` completo cada `full_sweep_interval_hours` (168 por defecto, `0` lo
  desactiva);
- `enrich` de todos los pendientes de ficha OPAC si no hay un descubrimiento o
  enriquecimiento activo.

El descubrimiento incremental reutiliza el `cursor_doc` y `cursor_titn` del ultimo
descubrimiento completado. El barrido completo semanal corrige posibles cambios
de orden del catalogo. Los jobs guardan `stats.mode` (`full` o `incremental`) y
`stats.reason`.

Si el OPAC devuelve un captcha que no se resuelve, el worker no consume el intento:
reencola el trabajo y pausa la ingesta `captcha_pause_minutes` minutos (30 por
defecto, configurable desde el dashboard).

Cuando un descubrimiento termina con nuevos registros, el worker encola
automaticamente un `enrich` con `stats.since = started_at` para priorizar lo
recien descubierto. El `enrich` programado, en cambio, encola sobre todos los
pendientes (sin `since`), sin limitarse a la ultima cohorte.

Tras completar un lote de enriquecimiento, el worker drena el backlog: si quedan
pendientes y el lote hizo progreso, encola el siguiente lote usando `cursor_titn`
para no repetir una cabeza de fallos. Al llegar al final, da una vuelta
(`cursor_titn` nulo) solo si el lote anterior hizo progreso; si un lote no
procesa ninguna ficha, el drenado se detiene. El tope de encadenamientos se
controla con `MEDIATECA_ENRICH_DRAIN_MAX_CHAIN` (100 por defecto; `0` lo
desactiva) y todo el drenado con `MEDIATECA_ENRICH_DRAIN_ENABLED`. Cada lote
guarda en `stats` `pending_after`, `pending_after_cursor`, `drain_chain`,
`drained` y `stop_reason` (`chain_forward`, `chain_wrap`, `no_pending`,
`no_progress`, `max_chain`, `disabled`, `already_active` o `enqueue_error`).

El dashboard permite encolar `discover`, `enrich` e `index` bajo demanda y editar
la programacion. Las acciones de escritura se protegen con
`MEDIATECA_DASHBOARD_ADMIN_TOKEN`: el operador introduce el token una vez y se
guarda en una cookie `HttpOnly` con `SameSite=Strict`.

## Dashboard de administracion

El dashboard sirve cuatro paginas con un menu lateral comun: Inicio (`/`),
Catálogo (`/catalogo`), Tareas (`/tareas`) y Configuracion (`/configuracion`).
Inicio muestra la salud del worker, el resumen de trabajos por estado y tipo, la
cobertura y las metricas. Catálogo es una vista de solo lectura del estado de
enriquecimiento por edicion, con resumen por estado OPAC y TMDB, filtros (estado,
texto, soporte, biblioteca, año, idioma y país, desaparición) y tabla paginada.
Tareas muestra la tabla de trabajos recientes y las acciones de descubrimiento,
enriquecimiento e indexacion. Configuracion agrupa la programacion, la URL de
FlareSolverr y el token de TMDB.

Inicio y Tareas incluyen `meta http-equiv="refresh"`; Configuracion y Catálogo no
lo incluyen para no perder los formularios ni los filtros. Las rutas POST
conservan su URL y redirigen a la pagina de origen con `message` o `error`; el
campo `next` se valida contra `/`, `/catalogo`, `/tareas` y `/configuracion`. El
estado de administracion y el login/logout viven en el menu lateral.

## Observabilidad de la ingesta

El dashboard sirve tambien la API de observabilidad, siempre de solo lectura:

- `GET /api/ingest/status`: trabajos recientes, cobertura, metricas y salud del worker.
- `GET /api/ingest/coverage`: cobertura, metricas y salud del worker.

La cobertura incluye ediciones descubiertas, enriquecidas, pendientes, fallidas y
desaparecidas, ademas del porcentaje de enriquecimiento. Las metricas agregan
fichas procesadas, errores, captchas detectados, captchas resueltos, captchas
fallidos, renovaciones de sesion y tiempo medio por ficha a partir de
`harvest_jobs.stats`. El estado del worker usa el fichero de
heartbeat y, como respaldo, el `heartbeat_at` de la base de datos; se marca
`degraded` tras 120 segundos sin senal.

La CLI ofrece el mismo resumen con `mediateca ingest-status`. Los jobs de ingesta
escriben logs JSON con `job_id`, `job_type`, `titn`, `doc`, `result`,
`duration_ms` y `error`; no se registran datos personales.

## Ejecucion

- `mediateca discover --max-pages N --limit M`: ejecuta el descubrimiento y crea
  stubs. Sin `--max-pages` ni `--limit` recorre el catalogo completo.
- `mediateca enrich --limit 5000`: ejecuta un lote de enriquecimiento. El limite
  por defecto es 5.000 fichas.
- `mediateca discover --index` y `mediateca enrich --index` indexan solo el lote
  procesado; el worker indexa automaticamente al terminar cada trabajo.
- `mediateca index --reset`: reconstruye el indice completo, solo para cambios de
  esquema o reparaciones.
- `mediateca ingest-status`: muestra trabajos, cobertura, metricas y salud del
  worker.
- `mediateca worker --concurrency N`: arranca el worker con N tareas paralelas;
  sin el flag usa la concurrencia guardada en el dashboard o el entorno.
- El worker procesa los trabajos `discover`, `enrich`, `index`, `tmdb` y
  `branches` de `harvest_jobs` con el mismo checkpoint y reanudacion.
