# Mediateca Madrid - enrich

Servicio de ingesta, descubrimiento, enriquecimiento, worker, scheduler e indexacion del catalogo de Mediateca Madrid dentro del monorepo. Escribe en PostgreSQL y Meilisearch; la API y el portal solo leen de esos almacenamientos.

## Arranque

```bash
cp .env.example .env
make up
```

El worker procesa `harvest_jobs`; el scheduler solo planifica. La API y el portal se despliegan desde el mismo stack. El worker puede ejecutar varias tareas compatibles a la vez: la concurrencia se configura con `MEDIATECA_WORKER_CONCURRENCY` (1-5) o desde `Configuracion` del dashboard y se aplica al reiniciar. Nunca coinciden dos trabajos del mismo tipo ni las parejas con dependencia `discover`/`enrich`, `enrich`/`tmdb`, `enrich`/`index` y `tmdb`/`index`; `branches` puede convivir con todos.

## Comandos

```bash
make help
make harvest q=cine pages=2 limit=20
make index
make worker-logs
make dashboard
make dashboard-logs
make test
make lint
make psql
```

El enriquecimiento completo se ejecuta en lotes de 5.000 fichas:

```bash
docker compose run --rm worker python -m mediateca enrich --limit 5000
```

A 1 peticion por segundo cada lote tarda aproximadamente 1,4 horas. El trabajo
guarda un cursor por `TITN`, reintenta las fichas fallidas y solo persiste datos
parseados: no crea snapshots HTML ni escribe en `MEDIATECA_RAW_DIR`.

El backfill de TMDB se ejecuta por lotes sobre las ediciones ya enriquecidas que
aun no tienen `tmdb_enriched_at`, y tambien sobre las que ya lo tienen pero
carecen de `tmdb_url` (por ejemplo, fichas sincronizadas antes de guardar las
portadas):

```bash
docker compose run --rm worker python -m mediateca tmdb-enrich --limit 5000 --delay 0.25
```

El comando reanuda por `TITN` las pendientes, no repite las ya sincronizadas y al
terminar indexa los TITN procesados; usa `--no-index` para omitir la indexacion.
Con `--refresh` vuelve a consultar TMDB tambien para las ediciones ya
sincronizadas, priorizando las de `tmdb_enriched_at` mas antiguo para rotar los
lotes. Las ediciones sin coincidencia quedan sin marca y se reintentan en
ejecuciones posteriores. La portada se guarda como URL de `image.tmdb.org` y el
enlace como ficha publica de TMDB, sin descargar imagenes. Requiere un token
guardado en el dashboard o `MEDIATECA_TMDB_API_TOKEN`.

La misma actualizacion TMDB puede lanzarse como trabajo manual desde `Tareas`
(`/tareas`) con un lote y la casilla "Reactualizar también las ya sincronizadas".
El trabajo se ejecuta en el worker, indexa los TITN procesados y no lo encola
nunca el scheduler: solo se lanza a mano desde el dashboard o la CLI.

## Normalización de títulos

El parser guarda el título propio completo, sin la mención de responsabilidad,
sin la puntuación ISBD final y sin calificadores de material como `[DVD-Vídeo]`.
Para corregir las ediciones que ya están guardadas sin volver a recolectar del
OPAC:

```bash
docker compose run --rm worker python -m mediateca normalize-titles --limit 100
```

Por defecto el comando es un dry-run: informa de cuántas ediciones cambiarían y
muestra ejemplos sin escribir. Revisa el informe, haz una copia de seguridad de
PostgreSQL y aplica los cambios con reindexado incremental:

```bash
docker compose run --rm worker python -m mediateca normalize-titles --apply --reindex
```

El comando recalcula el título desde `marc["T245ab"]`, `marc["T245"]` sin la
responsabilidad, `marc["ntitl"]` y el título actual. Descarta los candidatos con
corchetes desbalanceados, como el `T245ab` que algunos registros de Andalucía
cortan justo en `[`, y elimina los calificadores de material conocidos
(`[DVD-Vídeo]`, `[Vídeo]`, `[Blu-ray]`, etc.). No modifica obras ni ejemplares.
Es idempotente: una segunda ejecución no encuentra cambios.

Para corregir solo los calificadores de material de los títulos ya guardados,
sin recalcular desde MARC, usa el modo específico y limita la fuente:

```bash
docker compose run --rm worker python -m mediateca normalize-titles \
  --material-only --fuente andalucia --limit 100
docker compose run --rm worker python -m mediateca normalize-titles \
  --material-only --fuente andalucia --apply --reindex
```

Después del backfill puedes reconsultar TMDB por lotes para corregir países,
portadas y enlaces:

```bash
docker compose run --rm worker python -m mediateca tmdb-enrich --refresh --limit 5000
```

## Dashboard de estado

La vista web se divide en cuatro paginas con un menu lateral comun:

- `Inicio` (`/`): salud del worker, trabajos por estado y tipo, cobertura del
  catalogo y metricas de ingesta.
- `Catálogo` (`/catalogo`): vista del estado de enriquecimiento por edicion, con
  resumen por estado y tabla paginada filtrable por estado OPAC, estado TMDB,
  desaparicion, texto, soporte, biblioteca, año, idioma y país. Las ediciones en
  estado TMDB `unmatched` permiten asignar manualmente un ID de TMDB, que se
  valida contra TMDB antes de guardar la coincidencia.
- `Tareas` (`/tareas`): tabla de trabajos recientes y acciones de descubrimiento,
  enriquecimiento, indexacion y actualizacion de metadatos TMDB.
- `Configuracion` (`/configuracion`): programacion, concurrencia del worker, URL
  de FlareSolverr y token de TMDB.

El estado OPAC de una edicion puede ser `pending` (sin ficha), `enriched` (ficha
guardada) o `failed` (ultimo intento fallido). El estado TMDB puede ser `pending`
(sin intentar), `matched` (coincidencia), `unmatched` (sin coincidencia fiable),
`error` (consulta fallida) o `skipped` (sin token). Cada edicion conserva tambien
el numero de intentos y el ultimo error de cada capa.

Inicio y Tareas se refrescan automaticamente; Configuracion y Catálogo no, para
no perder los formularios ni los filtros. Las escrituras se limitan a las secciones
de configuracion, el encolado de trabajos y la asignacion manual de TMDB a
ediciones `unmatched`; no crea ni elimina ediciones, ejemplares ni entradas del
indice. Los mensajes de exito y error vuelven a la pagina donde se origino la
accion.

```bash
make dashboard        # Levanta el servicio dashboard en segundo plano
make dashboard-logs   # Sigue los logs del servicio
```

Queda disponible en `http://localhost:8080`. En local tambien se puede arrancar
con el comando de la CLI:

```bash
mediateca dashboard --host 127.0.0.1 --port 8080
```

La misma aplicacion expone la API de observabilidad de solo lectura:

```bash
curl http://localhost:8080/api/ingest/status
curl http://localhost:8080/api/ingest/coverage
```

Tambien se puede consultar desde la CLI:

```bash
docker compose run --rm worker python -m mediateca ingest-status
```

Variables de configuracion:

- `MEDIATECA_DASHBOARD_HOST` y `MEDIATECA_DASHBOARD_PORT`: host y puerto de escucha.
- `MEDIATECA_DASHBOARD_REFRESH_SECONDS`: intervalo de refresco automatico de la pagina.
- `MEDIATECA_DASHBOARD_RECENT_LIMIT`: numero de trabajos recientes mostrados.
- `MEDIATECA_DASHBOARD_WORKER_STALE_SECONDS`: antiguedad maxima del heartbeat antes
  de marcar el worker como `degraded`.

## FlareSolverr

La resolucion de captchas esta desactivada por defecto. Solo se usa cuando existe
una URL base de FlareSolverr, configurada con `MEDIATECA_FLARESOLVERR_URL` o desde
la seccion "Configuracion de FlareSolverr" del dashboard. La URL del dashboard se
guarda en la tabla `app_config` y prevalece sobre la variable de entorno.

- `MEDIATECA_FLARESOLVERR_URL`: URL base de la instancia de FlareSolverr, por
  ejemplo `http://flaresolverr:8191`.
- `MEDIATECA_FLARESOLVERR_MAX_TIMEOUT_MS`: tiempo maximo de resolucion en
  milisegundos. Por defecto, `60000`.

FlareSolverr se usa solo como fallback: la recoleccion normal sigue con `httpx` y
FlareSolverr se invoca unicamente cuando el OPAC devuelve un reCAPTCHA. Si no hay
URL configurada o la resolucion falla, el trabajo se detiene y se reprograma con
el backoff existente. No se incluye un servicio FlareSolverr en `docker-compose.yml`;
hay que apuntar la variable o la configuracion del dashboard a una instancia propia.

Eludir un captcha puede contravenir las condiciones de uso del OPAC: la funcion
esta desactivada por defecto y el operador asume la decision de activarla. No
expongas el dashboard publicamente sin autenticacion: la URL editable podria
apuntar a servicios internos (SSRF), aunque solo se aceptan URLs `http`/`https`
sin credenciales.

## TMDB

La obtencion del pais de origen con TMDB es opcional y esta desactivada mientras
no exista un token valido. El token puede ser una API Key v3 o un Read Access
Token v4; el cliente detecta el formato y usa `api_key` o `Authorization: Bearer`
segun corresponda.

El token se puede guardar desde la seccion "Configuracion de TMDB" del dashboard.
El valor guardado prevalece sobre `MEDIATECA_TMDB_API_TOKEN`; si no hay valor
guardado se usa la variable de entorno y, si tampoco existe, el enriquecimiento
TMDB se omite. El dashboard solo muestra una version enmascarada, no registra el
token en logs y permite borrarlo con una casilla explicita; guardar el campo vacio
conserva el token actual.

Variables de configuracion:

- `MEDIATECA_TMDB_API_TOKEN`: API Key v3 o Read Access Token v4.
- `MEDIATECA_TMDB_LANGUAGE`: idioma de busqueda; por defecto `es-ES`.
- `MEDIATECA_TMDB_DELAY`: segundos de espera entre peticiones; por defecto `0.25`.
- `MEDIATECA_TMDB_TIMEOUT`: timeout de cada peticion en segundos; por defecto `10`.
- `MEDIATECA_TMDB_MAX_RETRIES`: reintentos ante errores temporales; por defecto `3`.

El cliente consulta `/3/search/movie` para localizar la pelicula por titulo y ano
y `/3/movie/{id}` para obtener los paises de produccion. Si `production_countries`
esta vacio se usa `origin_country`. Los paises se guardan como codigos ISO 3166-1
alfa-2 en mayusculas y sin duplicados. El emparejamiento exige un ano dentro de
+-1 y una similitud de titulo de al menos 0,90, o coincidencia exacta si la ficha
no tiene ano.

TMDB limita el numero de peticiones. El cliente respeta `Retry-After`, aplica
backoff y usa el retardo configurado. El portal que muestre estos datos debe
incluir la atribucion exigida por TMDB ("This product uses the TMDB API but is
not endorsed or certified by TMDB."). No se cachean imagenes ni datos ajenos a
los campos normalizados del catalogo.

`paises_origen` se indexa como atributo filtrable y como faceta de Meilisearch.
Los lotes nuevos actualizan el indice de forma incremental; tras desplegar este
cambio o anadir el campo a un indice existente hay que reconstruirlo con
`mediateca index --reset`.

## Programacion y tareas bajo demanda

El stack incluye un servicio `scheduler` que no ejecuta el OPAC: solo encola
trabajos en `harvest_jobs`. Por defecto:

- busca novedades cada 12 horas mediante descubrimiento incremental;
- hace un barrido completo del catalogo cada 7 dias como red de seguridad;
- encola el enriquecimiento de todos los pendientes de ficha OPAC, sin limitarse
  a la ultima cohorte descubierta;
- drena el backlog: al terminar un lote con pendientes y progreso, encadena el
  siguiente lote con `cursor_titn` para no repetir una cabeza de fallos;
- reconcilia el indice de Meilisearch una vez por semana;
- evita duplicados si ya hay un trabajo activo del mismo tipo.

Los intervalos, el tamano de lote, el barrido completo y la activacion se guardan
en `app_config` y se editan desde la seccion "Programacion" de la pagina
Configuracion del dashboard.

La pagina Tareas tambien permite lanzar bajo demanda:

- "Buscar novedades": descubrimiento incremental.
- "Descubrimiento completo": recorre todo el catalogo.
- "Enriquecer pendientes": enriquece stubs pendientes.
- "Reindexar": encola una indexacion.

Variables relacionadas:

- `MEDIATECA_SCHEDULER_ENABLED`: valor por defecto si no hay configuracion en el
  dashboard.
- `MEDIATECA_SCHEDULER_POLL_SECONDS`: frecuencia con la que el scheduler revisa
  si toca encolar.
- `MEDIATECA_ENRICH_DRAIN_ENABLED`: activa o desactiva el drenado automatico del
  backlog de enriquecimiento (por defecto `true`).
- `MEDIATECA_ENRICH_DRAIN_MAX_CHAIN`: tope de lotes encadenados seguidos (100 por
  defecto; `0` desactiva el drenado).
- `MEDIATECA_DASHBOARD_ADMIN_TOKEN`: token necesario para las acciones de
  escritura del dashboard. Si queda vacio, las acciones estan abiertas.

La web publica consulta Meilisearch con el filtro `detail_complete=true`, por lo
que solo muestra fichas enriquecidas. Si el OPAC devuelve un captcha y no se
resuelve, el worker reencola el trabajo y pausa la ingesta durante los minutos
configurados en el dashboard.

## Modelo de datos y esquema

La edicion conserva `pais` con el codigo del MARC del OPAC y añade `paises_origen`
con la lista de codigos ISO 3166-1 alfa-2 obtenida de TMDB, `tmdb_id`,
`tmdb_poster_url` (URL de la portada en `image.tmdb.org`), `tmdb_url` (enlace a
la ficha de TMDB) y `tmdb_enriched_at`. La version del esquema compartido se
guarda en `schema_meta.schema_version`; este cambio la sube a `3`.

## Migraciones

- `scripts/migrate_disponibilidad.sql`: retirada del estado de prestamo.
- `scripts/migrate_ingesta.sql`: `harvest_jobs`, marcas de progreso, `schema_meta`
  y retirada idempotente de la tabla `snapshots`.
- `scripts/migrate_flaresolverr.sql`: tabla `app_config` para la configuracion
  persistida de FlareSolverr.
- `scripts/migrate_tmdb.sql`: columnas `paises_origen`, `tmdb_id`,
  `tmdb_poster_url`, `tmdb_url` y `tmdb_enriched_at`, indice de sincronizacion y
  `schema_version` 3.

Todas son idempotentes. `make migrate` requiere PostgreSQL levantado.

## OpenSpec

La planificacion de ingesta se consolido en `openspec/` en la raiz del monorepo.
