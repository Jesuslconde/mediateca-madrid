# Mediateca Madrid — ingesta y administración

`services/enrich` es el único módulo que escribe el catálogo. Descubre registros en catálogos AbsysNet, descarga y normaliza fichas, mantiene bibliotecas y sucursales, enriquece metadatos con TMDB, construye el índice de Meilisearch y expone un dashboard operativo.

También contiene las migraciones SQL, la cola `harvest_jobs`, el scheduler y los comandos de inicialización. La API pública y el portal no realizan estas tareas.

## Índice

- [Límites y componentes](#límites-y-componentes)
- [Estructura de archivos](#estructura-de-archivos)
- [Ejecución y procesos](#ejecución-y-procesos)
- [Configuración](#configuración)
- [Fuentes e identidad](#fuentes-e-identidad)
- [Cliente OPAC](#cliente-opac)
- [Descubrimiento](#descubrimiento)
- [Enriquecimiento](#enriquecimiento)
- [Persistencia del catálogo](#persistencia-del-catálogo)
- [Cola de trabajos](#cola-de-trabajos)
- [Concurrencia y recuperación](#concurrencia-y-recuperación)
- [Scheduler](#scheduler)
- [Indexación](#indexación)
- [TMDB](#tmdb)
- [Directorio de bibliotecas](#directorio-de-bibliotecas)
- [Agrupación y normalización](#agrupación-y-normalización)
- [Dashboard](#dashboard)
- [Observabilidad](#observabilidad)
- [Migraciones](#migraciones)
- [Comandos](#comandos)
- [Pruebas y desarrollo](#pruebas-y-desarrollo)

## Límites y componentes

| Componente | Entrada | Salida | Almacenamiento |
|---|---|---|---|
| `OpacClient` | URLs y formularios AbsysNet | HTML, cookies, sesión, métricas | Ninguno |
| `parser` | HTML de listado o detalle | `ParsedEdicion` | Ninguno |
| `Harvester` | Páginas OPAC y lote de TITN | Estadísticas y registros procesados | PostgreSQL |
| `repository` | `ParsedEdicion` | Altas y actualizaciones idempotentes | PostgreSQL |
| `MeiliIndexer` | Ediciones de PostgreSQL | Documentos de búsqueda | Meilisearch |
| `worker` | Trabajos pendientes | Trabajos completados o reprogramados | PostgreSQL + Meilisearch |
| `scheduler` | Reloj y `app_config` | Nuevos trabajos en cola | PostgreSQL |
| `dashboard` | Formularios y consultas SQL | HTML, redirecciones, JSON | PostgreSQL; Meilisearch al reindexar |

Reglas de propiedad:

- El catálogo lo escribe `services/enrich`.
- Las migraciones y `schema_meta` los actualiza este módulo.
- El índice lo crea y reconstruye `MeiliIndexer`.
- El dashboard puede modificar configuración, encolar trabajos, agrupar ediciones y corregir coincidencias TMDB; no elimina ediciones ni ejemplares.
- El portal no accede a estos almacenamientos directamente.

La operación común del stack está en [`docs/OPERATIONS.md`](../../docs/OPERATIONS.md).

## Estructura de archivos

```text
services/enrich/
├── src/mediateca/
│   ├── __main__.py                 # python -m mediateca
│   ├── cli.py                      # comandos Typer
│   ├── core/
│   │   ├── config.py               # Settings y variables MEDIATECA_*
│   │   ├── config_store.py         # app_config y precedencia de ajustes
│   │   ├── db.py                   # Engine, Session y session_scope
│   │   ├── logging.py              # logs JSON
│   │   ├── models.py               # tabla local app_config
│   │   └── scheduling.py           # programación persistida
│   ├── catalog/
│   │   ├── harvester.py            # OPAC, descubrimiento y enriquecimiento
│   │   ├── parser.py               # HTML -> ParsedEdicion
│   │   ├── repository.py           # upsert del catálogo
│   │   ├── fuentes.py              # semilla y selección de fuentes
│   │   ├── calibration.py          # detección de sesión y formato
│   │   ├── jobs.py                 # cola, handlers, worker y métricas
│   │   ├── scheduler.py            # encolado periódico
│   │   ├── indexer.py              # documentos y ajustes de Meilisearch
│   │   ├── tmdb.py                 # cliente y emparejamiento TMDB
│   │   ├── directory.py            # directorios HTML y JSON
│   │   ├── grouping.py             # obras y agrupación manual
│   │   └── title_backfill.py       # normalización de títulos existentes
│   ├── dashboard/                  # FastAPI + Jinja2
│   └── api/routers/ingest.py       # API de observabilidad del dashboard
├── scripts/migrate_*.sql           # migraciones idempotentes
├── fixtures/                       # HTML de pruebas
├── tests/                          # pytest
└── pyproject.toml
```

Las dependencias principales son SQLAlchemy 2, psycopg 3, Pydantic 2, httpx, BeautifulSoup/lxml, Meilisearch, FastAPI/Uvicorn, Jinja2, Typer, Tenacity y python-dateutil. El paquete se instala con Hatchling y expone el ejecutable `mediateca`.

## Ejecución y procesos

El mismo paquete arranca cuatro procesos distintos:

| Proceso | Punto de entrada | Función |
|---|---|---|
| Inicialización | `python -m mediateca init` | Crear esquema, migrar, limpiar listas e indexar |
| Worker | `python -m mediateca worker` | Reclamar y ejecutar trabajos |
| Scheduler | `python -m mediateca scheduler` | Decidir qué trabajos deben encolarse |
| Dashboard | `python -m mediateca dashboard` | Servir administración y observabilidad |

`docker/batch.Dockerfile` instala primero `packages/shared` y después este paquete en modo editable con sus dependencias de desarrollo. Por ello la imagen contiene también pytest, Ruff, mypy, fixtures y tests.

## Configuración

`core/config.py` usa `pydantic-settings` con prefijo `MEDIATECA_`, archivo `.env` y `extra="ignore"`. La instancia se cachea con `lru_cache`.

### Base, OPAC y registros

| Variable | Predeterminado | Uso |
|---|---|---|
| `MEDIATECA_DATABASE_URL` | PostgreSQL local | URL SQLAlchemy con `postgresql+psycopg` |
| `MEDIATECA_MEILISEARCH_URL` | `http://localhost:7700` | Endpoint de búsqueda |
| `MEDIATECA_MEILISEARCH_KEY` | `masterKey` | Credencial del cliente Meilisearch |
| `MEDIATECA_MEILISEARCH_INDEX` | `ediciones` | Índice del catálogo |
| `MEDIATECA_OPAC_BASE_URL` | Host de Madrid | Semilla de la fuente Madrid |
| `MEDIATECA_OPAC_PATH` | Ruta AbsysNet de Madrid | Semilla de la fuente Madrid |
| `MEDIATECA_CRAWL_DELAY` | `1.0` | Segundos entre peticiones OPAC |
| `MEDIATECA_CRAWL_TIMEOUT` | `30.0` | Timeout HTTP |
| `MEDIATECA_CRAWL_MAX_RETRIES` | `3` | Reintentos de transporte/sesión |
| `MEDIATECA_RAW_DIR` | `./data/raw` | Conservado por compatibilidad; no se escriben snapshots |
| `MEDIATECA_LOG_LEVEL` | `INFO` | Nivel de logs JSON |

### Worker y scheduler

| Variable | Predeterminado | Uso |
|---|---|---|
| `MEDIATECA_WORKER_CONCURRENCY` | `1` | Hilos de trabajo, entre 1 y 5 |
| `MEDIATECA_WORKER_POLL_SECONDS` | `5.0` | Espera cuando no hay trabajo |
| `MEDIATECA_WORKER_HEARTBEAT_SECONDS` | `30.0` | Heartbeat de trabajo y worker |
| `MEDIATECA_WORKER_HEARTBEAT_FILE` | `/tmp/mediateca-worker.heartbeat` | Señal compartida con el dashboard |
| `MEDIATECA_WORKER_STALE_SECONDS` | `120` | Recuperación de trabajos `running` estancados |
| `MEDIATECA_SCHEDULER_ENABLED` | `true` | Valor inicial si no hay ajuste persistido |
| `MEDIATECA_SCHEDULER_POLL_SECONDS` | `60` | Frecuencia de revisión del scheduler |
| `MEDIATECA_ENRICH_DRAIN_ENABLED` | `true` | Encadenar lotes de enriquecimiento |
| `MEDIATECA_ENRICH_DRAIN_MAX_CHAIN` | `100` | Tope de encadenamientos; `0` desactiva |

### Dashboard y servicios externos

| Variable | Predeterminado | Uso |
|---|---|---|
| `MEDIATECA_DASHBOARD_HOST` | `127.0.0.1` | Bind local |
| `MEDIATECA_DASHBOARD_PORT` | `8080` | Puerto |
| `MEDIATECA_DASHBOARD_REFRESH_SECONDS` | `15` | Refresco de Inicio y Tareas |
| `MEDIATECA_DASHBOARD_RECENT_LIMIT` | `20` | Trabajos recientes |
| `MEDIATECA_DASHBOARD_WORKER_STALE_SECONDS` | `120` | Umbral de salud del worker |
| `MEDIATECA_DASHBOARD_ADMIN_TOKEN` | vacío | Si está vacío, las escrituras quedan abiertas |
| `MEDIATECA_FLARESOLVERR_URL` | vacío | Fallback opcional de CAPTCHA |
| `MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS` | `60000` | `maxTimeout` de FlareSolverr |
| `MEDIATECA_TMDB_API_TOKEN` | vacío | API Key v3 o Read Access Token v4 |
| `MEDIATECA_TMDB_LANGUAGE` | `es-ES` | Idioma de consultas |
| `MEDIATECA_TMDB_DELAY` | `0.25` | Retardo entre peticiones |
| `MEDIATECA_TMDB_TIMEOUT` | `10` | Timeout HTTP |
| `MEDIATECA_TMDB_MAX_RETRIES` | `3` | Reintentos de errores temporales |

### Precedencia de `app_config`

La tabla local `app_config` guarda pares `key/value/text` y `updated_at`. Para FlareSolverr, TMDB, concurrencia y scheduler, el valor persistido válido prevalece sobre el entorno. Si se borra el valor persistido, se vuelve al entorno.

El token TMDB se muestra enmascarado y no se registra en logs. Guardar el campo vacío lo conserva; la casilla de borrado explícito elimina el valor. Los cambios de concurrencia se aplican al reiniciar el worker.

## Fuentes e identidad

La tabla `fuentes` contiene el perfil de cada catálogo:

- `codigo`, `nombre`, `adapter`.
- `base_url`, `opac_path`, `session_pattern`.
- `format_field`, `format_value`, `delay`.
- `enabled`, `paused_until`, `captcha_policy`.
- `options` JSON.

La identidad de una edición es:

```text
record_id = <codigo_fuente>:<TITN>
```

El TITN deja de ser único globalmente. Las restricciones son `UNIQUE(record_id)` y `UNIQUE(fuente_id, titn)`. Bibliotecas y sucursales son únicas por `(fuente_id, codigo)`; los ejemplares por `(fuente_id, external_key)`.

`FuenteProfile.from_model` adapta el modelo compartido al cliente. Las opciones relevantes son:

| Opción | Comportamiento |
|---|---|
| `discovery="avanzada"` | Formulario `FORM=2`, truncamiento `xsqf01=*` |
| `discovery="novedades"` | Formulario `FORM=5`, `xsqf99=1`, `select05` |
| `subcat` | Subcategoría enviada al OPAC |
| `search_extra` | Campos adicionales del formulario |
| `detail_on_discovery` | Descarga la ficha durante el descubrimiento |
| `coverage` | Marca una fuente de cobertura; el parser solo crea ejemplares si el OPAC los expone |
| `verify_tls` | Permite desactivar la verificación TLS de una fuente concreta |
| `directory` | Configuración de directorio HTML o JSON |
| `directory_path` | Ruta del directorio HTML de Madrid |

Madrid se siembra desde el entorno si no existe. Las fuentes autonómicas y CCBIP se siembran con migraciones y están deshabilitadas inicialmente. Una fuente deshabilitada no recibe nuevos trabajos de descubrimiento, enriquecimiento, TMDB o directorio, y esos comandos la rechazan; sus datos siguen consultables y aún puede calibrarse o reindexarse de forma explícita.

### Alta y calibración

```bash
docker compose run --rm worker python -m mediateca migrate
docker compose run --rm worker python -m mediateca calibrate-source --fuente aragon
docker compose run --rm worker python -m mediateca calibrate-source --fuente aragon --no-apply
docker compose run --rm worker python -m mediateca discover --fuente aragon --max-pages 1 --limit 5
docker compose run --rm worker python -m mediateca index --fuente aragon
```

`calibrate-source` abre sesión, detecta el segmento de sesión y busca una opción de video en `select03`. No habilita la fuente. Primero debe validarse un lote pequeño y después cambiar `enabled=true` desde el dashboard o la base.

Para revertir una fuente se deshabilita; no se borran sus ediciones ni se modifican las demás fuentes.

## Cliente OPAC

`OpacClient` encapsula `httpx.Client` y mantiene:

- Identificador de sesión y cookies.
- Patrón regex de sesión configurable.
- Modo de descubrimiento y campos de formulario.
- Contadores `captchas`, `captchas_solved`, `captchas_failed` y `session_renewals`.
- Cliente FlareSolverr perezoso, solo si hay URL.

### Sesión

1. `GET {opac_url}?ACC=101`.
2. Extracción del ID desde la URL final, el HTML o `URL=...`.
3. `GET {opac_url}/{session_id}?ACC=101` para inicializar cookies.

Si una petición detecta `timeout.htm` o `Sesión expirada`, renueva la sesión y sustituye el segmento de sesión de la URL. Durante la paginación profunda, vuelve a ejecutar la búsqueda y salta al siguiente `DOC`, porque una URL de listado depende del contexto de la sesión.

### CAPTCHA y FlareSolverr

La detección utiliza como señal principal `g-recaptcha`, `grecaptcha`, `recaptcha/api.js` o `g-recaptcha-response`. La frase “No soy un robot” solo se usa como respaldo cuando no pertenece al nodo oculto `hmsgopa1075` y la página no contiene listado, ficha o formulario OPAC.

FlareSolverr se invoca únicamente tras detectar un desafío real y si existe URL efectiva. Se usa su API v1 (`POST {url}/v1`) con `request.get` o `request.post`; se transfieren cookies y `postData`, y se importan las cookies y el `User-Agent` de la solución.

Si no hay resolver o la solución sigue siendo un CAPTCHA, se lanza `CaptchaRequired`. El worker no consume el intento, reencola el trabajo y pausa la fuente. La resolución está desactivada por defecto y debe cumplir las condiciones de uso del OPAC.

## Descubrimiento

El flujo `discover` enumera registros sin descargar todas las fichas:

1. Buscar `*` con el filtro de formato de video.
2. Recorrer enlaces `ACC=161&DOC=N`.
3. Parsear cada `li.c-docs_unit` con `parse_search_results`.
4. Descartar registros que `detect_audiovisual` clasifique como no audiovisuales.
5. Crear o actualizar un stub con `upsert_stub`.
6. Confirmar la página y guardar `cursor_doc`/`cursor_titn`.
7. Indexar los `record_id` procesados al terminar.

Un stub conserva metadatos básicos del listado y `discovery_seen_at`. Si ya existe una edición enriquecida, el upsert no sobrescribe sus campos completos; actualiza la fecha de visualización y limpia `missing_at`.

El cursor incremental procede del último descubrimiento completado. Si no hay cursor utilizable, `enqueue_discover_job` convierte el trabajo en `full`. En un barrido completo sin límites que haya procesado al menos un registro, las ediciones no vistas desde el inicio se marcan con `missing_at`; nunca se eliminan automáticamente.

`detail_on_discovery=true` permite que el descubrimiento descargue y guarde la ficha completa en la misma sesión, necesario para OPAC que no resuelven correctamente `?TITN=`.

## Enriquecimiento

El flujo `enrich` selecciona ediciones sin `detail_fetched_at`, ordenadas por TITN dentro de la fuente. Admite:

- `limit`: tamaño del lote; predeterminado 5000.
- `cursor_titn`: reanudación después del último TITN procesado.
- `since`: prioriza registros descubiertos desde una fecha.

Para cada registro:

1. `GET ?TITN=<titn>&FORM=1`.
2. `parse_detail`.
3. Descartar material no audiovisual o guardar con `upsert_edicion`.
4. Consultar TMDB si hay token.
5. Confirmar la transacción.
6. Actualizar cursor y estadísticas del trabajo.
7. Esperar el retardo configurado.

Los errores por ficha se reintentan con backoff exponencial. Un fallo terminal marca `enrich_status="failed"`, incrementa intentos, guarda el error y no bloquea el resto del lote. Un CAPTCHA sí aborta el lote para pausar la fuente.

Estados de una edición:

| Capa | Estado | Significado |
|---|---|---|
| OPAC | `pending` | Sin ficha completa |
| OPAC | `enriched` | Ficha guardada |
| OPAC | `failed` | Último intento fallido |
| TMDB | `pending` | Sin intentar |
| TMDB | `matched` | Coincidencia guardada |
| TMDB | `unmatched` | Sin coincidencia fiable |
| TMDB | `error` | Consulta fallida |
| TMDB | `skipped` | No hay token |

`enrich_attempts`, `enrich_last_attempt_at`, `enrich_last_error` y sus equivalentes TMDB permiten auditar cada capa. `tmdb_enriched_at` solo marca la última coincidencia.

Cuando el parser confirma que un registro no es audiovisual, `mark_non_audiovisual()` fija `detail_fetched_at`, `missing_at` y `enrich_status="skipped"`. Este último valor no está incluido en `ENRICH_STATUSES`, por lo que no aparece como opción en los filtros basados en esa constante.

## Persistencia del catálogo

`repository.py` traduce `ParsedEdicion` al modelo compartido:

- `record_id` compuesto con la fuente.
- Obra automática por título uniforme y año, salvo agrupación manual.
- Biblioteca por `(fuente_id, codigo)`.
- Personas normalizadas sin diacríticos y materias comparadas sin distinguir mayúsculas.
- Relaciones edición-persona, edición-materia y edición-enlace reconstruidas en cada enriquecimiento.
- Ejemplares sincronizados por `external_key`.

`external_key` es un SHA-1 de TITN, biblioteca, sucursal, signatura, soporte, tipo y código de barras. Se usa para evitar duplicados; no es un identificador criptográfico de seguridad.

Las transacciones se confirman por ficha o página. `session_scope` hace commit al salir y rollback si hay una excepción. El worker usa sesiones independientes por hilo y un `Engine` con `pool_pre_ping=True`.

No se guardan snapshots HTML. Aunque `MEDIATECA_RAW_DIR` y el volumen `raw_data` siguen presentes, el enriquecimiento actual solo persiste datos normalizados.

## Cola de trabajos

La tabla `harvest_jobs` almacena:

- `job_type`: `discover`, `enrich`, `index`, `tmdb` o `branches`.
- `status`: `pending`, `running`, `completed`, `failed` o `cancelled`.
- `fuente_id`; los trabajos de reindexación global no tienen fuente.
- `batch_size`, `cursor_doc`, `cursor_titn`.
- `attempts`, `max_attempts`, `started_at`, `finished_at`, `heartbeat_at`.
- `stats` JSON y `error`.

`DEFAULT_HANDLERS` conecta cada tipo con su implementación:

| Tipo | Handler | Resultado principal |
|---|---|---|
| `discover` | `_discover_handler` | Stubs, cursores e indexación incremental |
| `enrich` | `_enrich_handler` | Fichas OPAC + TMDB e indexación incremental |
| `index` | `_index_handler` | Reindexación de una fuente |
| `tmdb` | `_tmdb_handler` | Backfill TMDB e indexación |
| `branches` | `_branches_handler` | Directorio de bibliotecas |

`enqueue_job` rechaza duplicados si ya existe un trabajo del mismo tipo `pending` o `running` para la misma fuente. Eso evita duplicar acciones manuales o programadas; no impide que dos fuentes distintas procesen el mismo tipo en paralelo.

## Concurrencia y recuperación

El worker arranca entre 1 y 5 hilos. La precedencia es:

1. `--concurrency N` de CLI.
2. `worker_concurrency` guardado en `app_config`.
3. `MEDIATECA_WORKER_CONCURRENCY`.
4. `1` si el valor no es válido.

### Reclamo atómico

`claim_job`:

1. Obtiene `pg_advisory_xact_lock('mediateca:harvest_jobs:claim')`.
2. Lee los trabajos `running`.
3. Selecciona candidatos `pending` por fecha e ID.
4. Usa `FOR UPDATE SKIP LOCKED` en PostgreSQL.
5. Comprueba conflictos y pausas de fuente.
6. Marca el elegido `running`, incrementa `attempts` y fija heartbeat.

El lock solo serializa el reclamo dentro de su transacción; no mantiene bloqueada la ejecución del trabajo.

### Conflictos

Para una misma fuente no pueden coincidir:

- Dos trabajos del mismo tipo.
- `discover` con `enrich`.
- `enrich` con `tmdb`.
- `enrich` con `index`.
- `tmdb` con `index`.

`branches` es compatible con todos. Un trabajo de indexación sin fuente es exclusivo y bloquea cualquier otro trabajo. Los trabajos incompatibles permanecen `pending` hasta que desaparece el conflicto.

### Fallos y heartbeat

- Error normal: se reencola hasta `max_attempts`; después pasa a `failed`.
- CAPTCHA: se descuenta el intento consumido, se reencola y se fija `fuentes.paused_until`.
- Trabajo `running` sin heartbeat durante `MEDIATECA_WORKER_STALE_SECONDS`: se reencola o falla según los intentos disponibles.
- Cada trabajo actualiza `harvest_jobs.heartbeat_at`; el worker actualiza además el archivo de heartbeat.
- El backoff devuelto por `worker_tick` lo espera el hilo que procesó el fallo.

El worker no garantiza exclusión tipo a tipo entre fuentes distintas: aprovecha los cinco hilos para paralelizar fuentes, respetando los conflictos por fuente y el índice global.

## Scheduler

`scheduler` no descarga OPAC ni escribe Meilisearch; solo evalúa `app_config` y crea trabajos.

Valores predeterminados:

| Ajuste | Predeterminado |
|---|---|
| `discover_interval_hours` | 12 |
| `full_sweep_interval_hours` | 168; `0` desactiva |
| `enrich_interval_hours` | 12 |
| `enrich_batch_size` | 5000 |
| `index_interval_hours` | 168 |
| `captcha_pause_minutes` | 30 |

Por cada fuente habilitada y no pausada:

- Encola descubrimiento incremental o completo según corresponda.
- Encola enriquecimiento si hay pendientes y no hay descubrimiento/enriquecimiento activo.
- Encola una indexación de reconciliación si no hay trabajos incompatibles activos.

Tras un descubrimiento con registros procesados, el worker encola un enriquecimiento de la cohorte nueva con `since=started_at`. El enriquecimiento programado usa `since=None` para trabajar sobre todos los pendientes.

### Drenado del backlog

Al completar `enrich`, `maybe_chain_enrich` calcula si quedan pendientes:

- Avanza desde `cursor_titn` si hay registros posteriores.
- Vuelve al inicio si el lote avanzó y no hay posteriores.
- Se detiene si no hay pendientes, no hubo progreso, se alcanzó el tope o ya existe otro trabajo activo.

El trabajo guarda `pending_after`, `pending_after_cursor`, `drain_chain`, `drained` y `stop_reason`. Esto evita bloquearse indefinidamente en una cabeza de fichas fallidas.

## Indexación

`indexer.py` convierte cada edición en un documento Meilisearch. La clave primaria es `id`, derivada de `record_id` sustituyendo `:` por `_`; el documento conserva también `record_id`.

### Campos

Incluye, entre otros:

- Identidad: `record_id`, `fuente`, `fuente_nombre`, `titn`.
- Obra: `obra_id`, `obra_key`, `obra_titulo`.
- Bibliografía: título, título uniforme, publicación, año, idioma, país, duración, edad, sinopsis, géneros, materias, EAN.
- Personas: lista nombre/rol, directores, actores, guionistas y `personas_texto`.
- Soporte: `soportes`, `soporte_principal`.
- Disponibilidad: bibliotecas, ubicaciones, textos de ubicación y número de ejemplares.
- TMDB: países de origen, portada y enlace.
- Estado: `detail_complete`, `is_stub`, `updated_at`.

Las ubicaciones usan códigos estables `b:<fuente>:<biblioteca>` y `s:<fuente>:<sucursal>`. `ubicaciones_texto` conserva los nombres visibles para compatibilidad.

### Ajustes del índice

| Ajuste | Campos |
|---|---|
| Facetas | `soportes`, `generos`, `anio`, `idioma`, `paises_origen`, `bibliotecas`, `fuente` |
| Ordenación | `anio`, `titulo`, `duracion_min` |
| Búsqueda | Títulos, sinopsis, responsables, personas, materias, géneros, publicación y TITN |

Los filtrables incluyen identidad, fuente, soportes, género, año, idioma, país, países TMDB, bibliotecas, ubicaciones, duración, edad, estado de detalle y obra. El límite de paginación es 100000 hits y el de valores por faceta 100.

### Modos

- `index_titns(record_ids)`: indexa únicamente los identificadores indicados, en lotes de 200.
- `index_editions(reset=False)`: recorre todas las ediciones y actualiza documentos; no borra los ausentes.
- `index_editions(reset=True)`: borra el índice y lo reconstruye.
- `index --fuente <codigo>`: limita la reconstrucción a una fuente; no debe combinarse con `--reset` sin revisar el alcance, porque el borrado es global.

Los registros clasificados como no audiovisuales se excluyen. Un stub puede indexarse con `detail_complete=false`, pero la API de búsqueda pública añade el filtro `detail_complete=true`.

Si la indexación incremental falla, el worker conserva los identificadores en `stats.pending_index_titns` y los reintenta al reanudar. Un fallo del lote aún intenta indexar lo ya procesado.

## TMDB

`TmdbClient` detecta una API Key v3 o un Read Access Token v4:

- Key v3: parámetro `api_key`.
- Token v4 con formato JWT: cabecera `Authorization: Bearer`.

El emparejamiento:

1. Genera candidatos desde título uniforme y título.
2. Elimina calificadores de material/forma, responsabilidad y corchetes cuando procede.
3. Consulta `/3/search/movie`.
4. Exige año dentro de ±1 cuando la edición tiene año.
5. Exige similitud de título ≥ 0,90; si no hay año, exige coincidencia exacta normalizada.
6. Consulta `/3/movie/{id}` para detalle.
7. Guarda `production_countries`; si está vacío, usa `origin_country`.
8. Normaliza códigos ISO 3166-1 alfa-2, mayúsculas y sin duplicados.

Las portadas se guardan como URL de `image.tmdb.org/t/p/w500`; no se descargan imágenes. Se guarda también el enlace público de TMDB.

El cliente respeta `Retry-After`, reintenta 429, 5xx y errores de transporte con backoff, y no reintenta tokens inválidos ni recursos inexistentes. Los logs HTTP de httpx/httpcore se bajan a `WARNING` para no filtrar la API Key v3.

El job `tmdb`:

- No lo encola nunca el scheduler.
- Selecciona ediciones enriquecidas sin `tmdb_enriched_at` o con `tmdb_id` pero sin `tmdb_url`.
- Con `refresh`, también consulta las ya sincronizadas, priorizando las más antiguas.
- Indexa los identificadores procesados al terminar.
- Sin token, falla de forma explícita.

## Directorio de bibliotecas

`directory.py` admite dos clientes:

| Cliente | Fuente | Formato |
|---|---|---|
| `DirectoryClient` | Comunidad de Madrid | HTML con listados y fichas |
| `OpenDataDirectoryClient` | Junta de Andalucía | JSON de datos abiertos |

El parser normaliza `ParsedSucursal`: biblioteca, sucursal, nombre, municipio, dirección, código postal de cinco dígitos, coordenadas y condición móvil. Las bibliotecas móviles no conservan coordenadas.

La política la declara `options.directory.mode`:

- `match`: solo procesa bibliotecas conocidas de la fuente.
- `create`: puede crear bibliotecas y sucursales ausentes.

`refresh_sucursales` actualiza campos no vacíos, no borra bibliotecas ausentes del directorio y no crea ediciones ni ejemplares. El emparejamiento utiliza el código SUBC; sin código, puede usar nombre normalizado y municipio cuando la coincidencia es única.

El trabajo `branches` usa la política `match/create` de la fuente. El comando directo `refresh-branches` hace lo mismo de forma síncrona. Para probar:

```bash
make branches branches_limit=20
docker compose run --rm worker python -m mediateca refresh-branches --fuente andalucia --limit 20
```

## Agrupación y normalización

### Obras automáticas y manuales

La agrupación automática utiliza título uniforme y año. `upsert_edicion` conserva la obra de una edición si `obra_manual=true`, evitando que una nueva recolección rompa una decisión del operador.

`grouping.py` permite:

- Mover ediciones a una obra existente.
- Crear o reutilizar una obra por título uniforme y año.
- Marcar como manuales todas las ediciones de la obra destino.
- Desvincular una edición y recalcular su obra automática.
- Eliminar obras que quedan sin ediciones y recalcular `obras.manual`.

Después de agrupar o desvincular, el dashboard confirma PostgreSQL y reindexa solo los `record_id` afectados. Si Meilisearch falla, la decisión persiste y se muestra una advertencia.

### Normalización de títulos

`normalize-titles` recalcula títulos desde el MARC guardado, sin volver al OPAC:

```bash
docker compose run --rm worker python -m mediateca normalize-titles --limit 100
docker compose run --rm worker python -m mediateca normalize-titles --apply --reindex
docker compose run --rm worker python -m mediateca normalize-titles \
  --material-only --fuente andalucia --limit 100
```

Sin `--apply` es un dry-run. El orden de candidatos es `T245ab`, `T245a`, `T245` sin responsabilidad, `ntitl` y título actual. Se descartan candidatos con corchetes desbalanceados y se eliminan calificadores conocidos como `[DVD-Vídeo]`, `[Vídeo]` o `[Blu-ray]`.

`--material-only` limpia únicamente el calificador del título actual. `--reindex` solo tiene efecto con `--apply` y actualiza los documentos modificados.

### Soportes

El paquete compartido normaliza `4K UHD`, `Blu-ray`, `DVD` y `VHS`. Se excluyen del índice materiales no audiovisuales como CD-ROM, DVD-ROM, CD-DA, discos sonoros y diapositivas. La clasificación combina descripción física, tipo de documento y soportes de ejemplares.

## Dashboard

FastAPI monta las plantillas Jinja2 y el router de observabilidad. No es el portal público.

### Páginas

| Ruta | Contenido |
|---|---|
| `/` | Salud, trabajos por estado/tipo/fuente, cobertura y métricas |
| `/catalogo` | Estado OPAC/TMDB, filtros y paginación |
| `/agrupacion` | Selección y corrección de obras |
| `/agrupacion/ediciones` | Detalle de ediciones seleccionables |
| `/tareas` | Lanzamiento de trabajos, fuentes y trabajos recientes |
| `/configuracion` | Programación, concurrencia, FlareSolverr y TMDB |
| `/health` | Comprobación de PostgreSQL |

Inicio y Tareas se refrescan mediante `/api/dashboard/inicio` y `/api/dashboard/tareas`. Catálogo, Agrupación y Configuración no se refrescan automáticamente para no perder filtros o formularios.

### Escrituras

Las rutas POST cubren login/logout, configuración, trabajos individuales y por lote, estado de fuentes, asignación manual de TMDB y agrupación. Todas las operaciones de escritura comprueban `_has_write_access`; login y logout son las excepciones porque precisamente gestionan esa credencial.

Si `MEDIATECA_DASHBOARD_ADMIN_TOKEN` está configurado:

- Se acepta la cookie `mediateca_admin` o la cabecera `X-Admin-Token`.
- El login emite una cookie `HttpOnly`, `SameSite=Strict`, de ocho horas.
- Las redirecciones `next` se validan contra una lista de rutas permitidas.
- Los formularios devuelven errores mediante `303` a la página de origen.

Si el token está vacío, el dashboard queda en modo sin autenticación. Debe limitarse a una red confiable.

La asignación manual de TMDB solo se permite para ediciones `unmatched`; el ID se valida contra la API antes de guardar.

## Observabilidad

El router incluido en `/api` expone:

| Ruta | Respuesta |
|---|---|
| `/api/ingest/status?limit=20` | Trabajos recientes, cobertura, métricas y worker |
| `/api/ingest/coverage` | Cobertura, métricas y worker |

Un error SQLAlchemy devuelve `503`. `limit` está acotado entre 1 y 100.

La cobertura distingue:

- `descubiertas`: tienen `discovery_seen_at`.
- `enriquecidas`: tienen `detail_fetched_at`.
- `pendientes`: siguen siendo stub o no tienen detalle.
- `fallidas`: longitud de las listas de fallos acumuladas en `stats`.
- `desaparecidas`: tienen `missing_at`.

Las métricas agregan `processed`, `errors`, captchas detectados/resueltos/fallidos, renovaciones de sesión, fallos, pendientes y tiempo medio por ficha. Se calculan a partir de `harvest_jobs.stats`, no de una tabla de series temporales.

La salud del worker usa primero el archivo de heartbeat y, si no existe, el máximo `heartbeat_at` de trabajos `running`. Sin señal o con más de 120 segundos de antigüedad se marca `degraded`.

Los logs usan JSON con campos como `job_id`, `job_type`, `fuente`, `record_id`, `titn`, `doc`, `result`, `duration_ms`, `error`, `step`, `path`, `method`, `status_code`, `rows`, `page` y `pool_status`.

## Migraciones

Los scripts se aplican por orden lexicográfico dentro de una transacción:

| Script | Cambio principal |
|---|---|
| `migrate_disponibilidad.sql` | Retira el estado de préstamo |
| `migrate_ingesta.sql` | Cola, carreras, `schema_meta` y retirada de snapshots |
| `migrate_fuentes.sql` | Fuentes, identidad compuesta y backfill a Madrid |
| `migrate_sucursales_geo.sql` | Sucursales y ubicación de ejemplares |
| `migrate_listas.sql` | Listas de favoritos |
| `migrate_flaresolverr.sql` | `app_config` |
| `migrate_tmdb.sql` | Países, ID, portada, enlace y fecha TMDB |
| `migrate_enriquecimiento_estado.sql` | Estados e intentos OPAC/TMDB |
| `migrate_andalucia.sql` | Fuente Andalucía |
| `migrate_andalucia_directory.sql` | Directorio abierto andaluz |
| `migrate_fuentes_autonomicas.sql` | Diez fuentes autonómicas |
| `migrate_fuentes_cobertura.sql` | Cinco fuentes CCBIP |
| `migrate_agrupacion_manual.sql` | Agrupación manual de obras |

Todos deben ser idempotentes. `Base.metadata.create_all` crea tablas ausentes en bases nuevas, pero no sustituye las migraciones para bases existentes. Al terminar, CLI fuerza el valor de `schema_meta` con `key='schema_version'` al valor de `mediateca_shared.version.SCHEMA_VERSION`.

## Comandos

Ejecutados desde la raíz del monorepo:

```bash
make test-enrich
make lint
make worker-logs
make dashboard
make dashboard-logs
make psql
```

Dentro del contenedor o en un entorno local con el paquete instalado:

```bash
mediateca --help
mediateca init
mediateca migrate
mediateca worker --concurrency 3
mediateca worker --once
mediateca scheduler --once
mediateca discover --fuente madrid --max-pages 1 --limit 5 --index
mediateca enrich --fuente madrid --limit 100 --index
mediateca tmdb-enrich --fuente madrid --limit 100 --refresh
mediateca normalize-titles --limit 100
mediateca index
mediateca index --reset
mediateca index --fuente andalucia
mediateca refresh-branches --fuente madrid --limit 20
mediateca enqueue-branches --fuente madrid
mediateca calibrate-source --fuente aragon --no-apply
mediateca parse-file services/enrich/fixtures/detail_dvd.html
mediateca status
mediateca ingest-status
mediateca dashboard --host 127.0.0.1 --port 8080
```

`harvest` está orientado a búsquedas concretas y descarga fichas completas. Para enumeración del catálogo y reanudación por cursor se usa `discover`.

## Pruebas y desarrollo

```bash
docker compose run --rm --no-deps worker pytest -q
docker compose run --rm --no-deps worker ruff check src tests /app/packages/shared/src /app/packages/shared/tests
docker compose run --rm --no-deps worker ruff format --check src tests /app/packages/shared/src /app/packages/shared/tests
make test-migrations
```

Las pruebas cubren parser, cliente OPAC, sesiones y CAPTCHA, repositorio, descubrimiento, enriquecimiento, TMDB, indexación, cola y scheduler, directorio, agrupación, dashboard, configuración, observabilidad, calibración, CLI y migraciones. Las fixtures HTML permiten probar variantes de AbsysNet sin depender de la red.

Para desarrollo local:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ./packages/shared
pip install -e 'services/enrich[dev]'
pytest services/enrich/tests -q
```

Las pruebas que requieren PostgreSQL deben recibir una URL de prueba adecuada. No uses la base de producción para `test-migrations`.

## Documentación relacionada

- [Modelos y esquemas compartidos](../../packages/shared/README.md)
- [API pública](../../services/api/README.md)
- [Portal](../../apps/web/README.md)
- [Arquitectura de ingesta](../../docs/ARCHITECTURE_ENRICH.md)
- [Operación y despliegue](../../docs/OPERATIONS.md)
