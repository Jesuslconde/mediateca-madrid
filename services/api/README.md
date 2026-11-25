# Mediateca Madrid — API

`services/api` es la API FastAPI del portal. Sirve búsqueda y facetas desde Meilisearch, fichas y ubicaciones desde PostgreSQL, y gestiona listas de favoritos persistentes.

Es una API de **lectura del catálogo**, no una API completamente de solo lectura: su única escritura en PostgreSQL son las tablas `listas` y `lista_items`. Las migraciones y las escrituras del catálogo pertenecen a `services/enrich`.

## Índice

- [Responsabilidades y límites](#responsabilidades-y-límites)
- [Estructura](#estructura)
- [Configuración y arranque](#configuración-y-arranque)
- [PostgreSQL e identidad](#postgresql-e-identidad)
- [Meilisearch y búsqueda](#meilisearch-y-búsqueda)
- [Rutas](#rutas)
- [Listas de favoritos](#listas-de-favoritos)
- [Middleware y seguridad](#middleware-y-seguridad)
- [OpenAPI](#openapi)
- [Pruebas y comandos](#pruebas-y-comandos)
- [Limitaciones actuales](#limitaciones-actuales)

## Responsabilidades y límites

| Componente | PostgreSQL | Meilisearch |
|---|---|---|
| `services/enrich` | Migraciones y escritura del catálogo | Creación, settings y escritura |
| `services/api` | Lectura del catálogo; escritura de listas | Solo lectura |
| `apps/web` | Sin acceso directo | Sin acceso directo |
| `packages/shared` | Modelos y esquemas | Define el subconjunto público de documentos |

La API:

- Busca en Meilisearch y devuelve facetas.
- Agrupa resultados por obra y completa agregados desde PostgreSQL.
- Serializa fichas, bibliotecas, sucursales y estadísticas.
- Comprueba la versión del esquema antes de aceptar tráfico.
- Crea y modifica listas identificadas por tokens opacos.
- Exporta el contrato OpenAPI consumido por el portal.

La API no crea tablas, no aplica migraciones, no escribe documentos de Meilisearch y no reconstruye el índice.

## Estructura

```text
services/api/
├── src/mediateca/
│   ├── api/
│   │   ├── main.py                 # app, lifespan, CORS y routers
│   │   ├── deps.py                  # get_db y get_indexer
│   │   ├── schemas.py               # reexporta esquemas compartidos
│   │   ├── serializers.py           # Edicion -> RecordDetail
│   │   ├── aggregation.py           # hits -> obras agregadas
│   │   └── routers/
│   │       ├── search.py
│   │       ├── records.py
│   │       ├── libraries.py
│   │       ├── lists.py
│   │       └── health.py
│   ├── core/
│   │   ├── config.py                # Settings
│   │   ├── db.py                    # Engine, sesiones y check_schema
│   │   ├── search.py                # cliente Meilisearch cacheado
│   │   └── logging.py               # TokenMaskFilter
│   └── catalog/search.py            # CatalogSearch de solo lectura
├── scripts/export_openapi.py
├── tests/
│   ├── test_api.py
│   └── test_lists.py
└── pyproject.toml
```

Dependencias runtime: FastAPI, Uvicorn, SQLAlchemy 2, psycopg 3, Pydantic 2, pydantic-settings y el cliente Meilisearch. Python admitido: `>=3.11,<3.15`.

El paquete `mediateca-shared` no se declara como dependencia publicada en `pyproject.toml`; se instala desde la ruta local al construir la imagen.

## Configuración y arranque

`Settings` usa prefijo `MEDIATECA_`, archivo `.env`, UTF-8 y `extra="ignore"`. `get_settings()` se cachea con `lru_cache`.

| Variable | Predeterminado | Uso |
|---|---|---|
| `MEDIATECA_DATABASE_URL` | PostgreSQL local | Engine SQLAlchemy |
| `MEDIATECA_MEILISEARCH_URL` | `http://localhost:7700` | Cliente Meilisearch |
| `MEDIATECA_MEILISEARCH_KEY` | `masterKey` | Credencial de Meilisearch |
| `MEDIATECA_MEILISEARCH_INDEX` | `ediciones` | Índice de búsqueda |
| `MEDIATECA_API_CORS_ORIGINS` | `http://localhost:3000` | Orígenes separados por comas |
| `MEDIATECA_LOG_LEVEL` | `INFO` | Nivel de logging |
| `MEDIATECA_ENVIRONMENT` | `development` | Declarada; no altera el comportamiento actual |
| `MEDIATECA_OPAC_BASE_URL` | Host de Madrid | No usada por la API |
| `MEDIATECA_OPAC_PATH` | Ruta de Madrid | No usada por la API |

Los enlaces OPAC no usan esas dos últimas variables. Se construyen a partir de la fila `Fuente` de PostgreSQL mediante `FuenteProfile.source_url()`. Si falta la relación, se usa el perfil Madrid estático. `Edicion.source_url` no lo utilizan los serializadores actuales.

### Lifespan y esquema

Al arrancar, `lifespan()`:

1. Configura logging.
2. Ejecuta `check_schema()`.
3. Si falla, registra el error y relanza la excepción, abortando Uvicorn.

`check_schema()` consulta:

```sql
SELECT value FROM schema_meta WHERE key = 'schema_version'
```

Después exige igualdad exacta con `SCHEMA_VERSION`, actualmente `"8"`.

- Fila ausente o valor distinto: `SchemaVersionError`.
- Tabla inexistente o base inaccesible: se propaga la excepción SQLAlchemy original.
- La API no crea tablas ni corrige el esquema.

El engine y la factoría de sesiones son perezosos. El engine usa `pool_pre_ping=True`; las sesiones tienen `autoflush=False`, `autocommit=False` y `expire_on_commit=False`. `get_db` cierra la sesión, pero no hace commit automático.

### Docker

No hay un Dockerfile propio. La API se ejecuta desde `mediateca-web`, construida por [`docker/web.Dockerfile`](../../docker/web.Dockerfile), que también contiene el portal.

En Compose:

```bash
/opt/venv/bin/uvicorn mediateca.api.main:app --host 0.0.0.0 --port 8000
```

El servicio `api` publica `${API_PORT:-8000}:8000`, depende de que `init` termine y de que Meilisearch esté started. No tiene healthcheck propio. Portainer usa la misma imagen y un `init` basado en comandos separados.

## PostgreSQL e identidad

### Tablas utilizadas

La API lee:

- `fuentes`, `obras`, `ediciones`.
- `bibliotecas`, `sucursales`, `ejemplares`.
- `personas`, `edicion_persona`.
- `materias`, `edicion_materia`.
- `enlaces`, `schema_meta`.

Escribe únicamente `listas` y `lista_items`. Aunque `Base` registra `harvest_jobs` y `harvest_runs`, la API no los consulta.

### Identidad

La identidad canónica es:

```text
<fuente>:<titn>
```

`normalize_record_id()` admite:

- `madrid:2101557`.
- `2101557`, resuelto como `madrid:2101557`.

Validaciones:

- Fuente: `^[a-z0-9][a-z0-9-]*$`.
- TITN: hasta 32 caracteres y `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
- Identidad vacía, con varios separadores o con fuente en mayúsculas: inválida.

Restricciones del modelo:

- `Edicion`: único por `(fuente_id, titn)` y por `record_id`.
- `Biblioteca`: único por `(fuente_id, codigo)`.
- `Sucursal`: único por `(fuente_id, codigo)`.
- `Ejemplar`: único por `(fuente_id, external_key)`.

### Ficha

`get_record()`:

1. Normaliza `record_id`.
2. Busca la edición.
3. Carga eagermente fuente, obra, ejemplares con biblioteca/sucursal, personas, materias y enlaces.
4. Si hay obra, consulta sus ediciones hermanas ordenadas por año y TITN.
5. Serializa con `serialize_record()`.

`serialize_record()`:

- Convierte materias a términos y personas a `{nombre, rol}`.
- Conserva enlaces, ejemplares, notas y MARC.
- Construye `source_url` desde el perfil de fuente.
- Devuelve `updated_at` como ISO string o `null`.
- Incluye `obra.ediciones` con un resumen de cada edición hermana.

### Ubicación de ejemplares

`_ubicacion()` elige la sucursal si la relación se resuelve. Solo usa la biblioteca cuando no hay sucursal.

No hay fallback campo a campo:

- Una sucursal sin coordenadas devuelve `latitud`/`longitud` como `null`, aunque la biblioteca las tenga.
- Sin sucursal, se usan los datos de biblioteca.
- Si no hay ningún dato, `ubicacion` completa es `null`.

La relación `Ejemplar.sucursal` es `viewonly=True` y se resuelve por `(fuente_id, sucursal_codigo)`, sin clave foránea directa.

### Bibliotecas, ubicaciones y estadísticas

`GET /api/libraries`:

- Devuelve todas las bibliotecas, incluso con cero ejemplares.
- Cuenta ejemplares con `OUTER JOIN`.
- Ordena por nombre.
- No filtra fuentes deshabilitadas.

`GET /api/locations`:

- Deriva bibliotecas y sucursales de los ejemplares.
- Códigos: `b:<fuente>:<codigo>` y `s:<fuente>:<codigo>`.
- Puede incluir una sucursal sin fila en `sucursales` gracias al `OUTER JOIN`.
- El municipio de sucursal cae al de biblioteca si hace falta.
- No lista sucursales sin ejemplares.

`GET /api/stats`:

- Carga las ediciones en memoria.
- Cuenta ediciones, ejemplares y bibliotecas.
- `por_soporte` recorre `Edicion.soportes`; no cuenta `Ejemplar.soporte`.
- Una edición con dos soportes incrementa ambos contadores.
- No excluye stubs, fuentes deshabilitadas ni registros desaparecidos.

## Meilisearch y búsqueda

### Adaptador de solo lectura

`CatalogSearch` usa el cliente y el índice cacheados de `core/search.py`. No crea el índice, no cambia settings, no escribe documentos y no reindexa.

El indexador de `services/enrich` define:

- Clave primaria `id = record_id.replace(":", "_")`.
- `record_id`, `detail_complete`, `is_stub`, `obra_key`, `obra_id`, bibliotecas y ubicaciones.
- Lotes de 200 documentos.
- Facetas de soportes, géneros, año, idiomas, países, bibliotecas y fuente.
- Ordenación por año, título y duración.
- `pagination.maxTotalHits=100000`.
- `faceting.maxValuesPerFacet=100`.

### Filtros

La API añade siempre:

```text
detail_complete = true
```

Los filtros adicionales se combinan con AND:

| Parámetro | Filtro |
|---|---|
| `titn` | `titn = "<valor>"` |
| `fuente` | `fuente = "<valor>"` |
| `soporte` repetido | OR entre `soportes = "<valor>"` |
| `genero` | `generos = "<valor>"` |
| `idioma` | `idioma = "<valor>"` |
| `paises_origen` repetido | OR entre `paises_origen = "<valor>"` |
| `biblioteca` con `b:`/`s:` | `ubicaciones = "<codigo normalizado>"` |
| `biblioteca` como texto | `bibliotecas` o `ubicaciones_texto` |
| `anio_desde` | `anio >= N` |
| `anio_hasta` | `anio <= N` |

Los valores textuales escapan comillas dobles y barras invertidas. Los códigos históricos `b:CODIGO` y `s:CODIGO` se normalizan a Madrid.

No hay enum cerrado de soportes ni validación de formato ISO para países. La descripción de OpenAPI no se convierte en validación runtime.

### Búsqueda en dos pasadas

1. **Resultados paginados**
   - `distinct="obra_key"`.
   - Página, límite, filtros, facetas, highlighting y orden.
   - Proporciona `total`, `hits` y `took_ms`.

2. **Totales y facetas sin agrupar**
   - `hitsPerPage=1`.
   - Sin `distinct`.
   - Mismos filtros y orden.
   - Proporciona `total_ediciones` y `facetDistribution`.

Consecuencias:

- `total` cuenta obras/grupos paginables.
- `total_ediciones` cuenta ediciones completas que coinciden.
- Las facetas proceden de ediciones, no de obras agregadas.
- `took_ms` solo refleja la primera consulta.
- `total_pages` se calcula con `total` y `limit`, con mínimo 1.

Si Meilisearch no devuelve total, se prueba `estimatedTotalHits`, después `totalHits` y después el número de hits. Si no devuelve facetas o tiempo, se usan `{}` y `0`.

### Agregación desde PostgreSQL

`aggregate_hits_by_obra()` carga las ediciones de los `obra_id` devueltos y completa cada hit con:

- Número real de ediciones.
- Soportes ordenados de ediciones y ejemplares.
- Bibliotecas ordenadas.
- Total de ejemplares.
- Título de obra si falta.
- Primer valor no vacío de póster, año, duración, sinopsis o título uniforme.

La agregación incluye todas las ediciones de la obra, no solo las que cumplen individualmente el filtro. Si hay un filtro de biblioteca o sucursal activo, en cambio, solo se cuentan los ejemplares que coinciden con ese filtro y se descartan las obras sin ningún ejemplar en la ubicación seleccionada. Si no hay obra o no se encuentran ediciones, `ediciones_count` queda en `1`.

No existe fallback de búsqueda a PostgreSQL. Un fallo de Meilisearch produce 503; un índice vacío o desactualizado se devuelve tal cual.

## Rutas

| Método | Ruta | Respuesta correcta |
|---|---|---|
| GET | `/` | 200, metadatos |
| GET | `/health` | 200, estado de dependencias |
| GET | `/api/search` | 200, `SearchResponse` |
| GET | `/api/records/{record_id}` | 200, `RecordDetail` |
| GET | `/api/libraries` | 200, lista de bibliotecas |
| GET | `/api/locations` | 200, lista de ubicaciones |
| GET | `/api/stats` | 200, `StatsResponse` |
| POST | `/api/lists` | 201, token |
| GET | `/api/lists/{token}` | 200, lista |
| POST | `/api/lists/{token}/items` | 201 nuevo; 200 existente |
| DELETE | `/api/lists/{token}/items/{record_id}` | 200, mutación |
| PATCH | `/api/lists/{token}` | 200, lista renombrada |

FastAPI expone además `/openapi.json`, `/docs` y `/redoc`.

### `GET /api/search`

| Parámetro | Tipo/default | Validación |
|---|---|---|
| `q` | string, `""` | Máximo 250; no se recorta |
| `titn` | string opcional | Máximo 32; filtro exacto |
| `soporte` | lista repetible | Sin enum; OR |
| `genero` | string opcional | Valor exacto |
| `anio_desde` | entero opcional | 1900–2100 |
| `anio_hasta` | entero opcional | 1900–2100 |
| `idioma` | string opcional | Valor exacto |
| `paises_origen` | lista repetible | OR |
| `biblioteca` | string opcional | Código o nombre |
| `fuente` | string opcional | Código exacto |
| `page` | entero, `1` | `>=1` |
| `limit` | entero, `20` | 1–100 |
| `sort` | string, `relevancia` | Whitelist |
| `disponible` | retirado | Si aparece, 400 |

Valores de `sort`:

| Valor | Criterios |
|---|---|
| `relevancia` | Se omite `sort` |
| `anio_desc` | `anio:desc`, `titulo:asc` |
| `anio_asc` | `anio:asc`, `titulo:asc` |
| `titulo_asc` | `titulo:asc` |
| `duracion_asc` | `duracion_min:asc`, `titulo:asc` |

Errores propios:

- 400 si existe `disponible`, incluso vacío.
- 400 si `sort` no está permitido.
- 400 si `anio_desde > anio_hasta`.
- 503 si falla la búsqueda Meilisearch: `"El indice de busqueda no esta disponible"`.
- 422 de FastAPI para tipos o límites inválidos.

Los parámetros desconocidos se ignoran salvo `disponible`.

### Respuesta de búsqueda

`SearchResponse` contiene `query`, `page`, `limit`, `total`, `total_ediciones`, `total_pages`, `took_ms`, `facets` y `hits`.

`SearchHit` incluye, entre otros:

- Identidad: `id`, `record_id`, `fuente`, `fuente_nombre`, `titn`, `titulo`.
- Obra: `obra_id`, `obra_titulo`, `ediciones_count`.
- Bibliografía: título uniforme, publicación, año, idioma, país, países TMDB.
- TMDB: póster y enlace.
- Contenido: duración, edad, sinopsis, géneros, materias y soportes.
- Disponibilidad: bibliotecas y ejemplares.
- Créditos: directores, actores y guionistas.
- Resaltado: `_formatted`, con título y sinopsis.

El resaltado usa `<mark>`. Los campos del documento no declarados en `SearchHit` se descartan por Pydantic.

### `GET /api/records/{record_id}`

Acepta `madrid:2101557` o `2101557`.

Errores:

- 422 con `detail` string si falla `normalize_record_id()`.
- 404: `"No existe el registro <record_id>"`.

`RecordDetail` incluye identidad, bibliografía, TMDB, contenido, soportes, personas, enlaces, ejemplares, obra, notas, MARC, `source_url` y `updated_at`.

`ObraOut` incluye `id`, `titulo_uniforme`, `anio`, `director_principal` y `ediciones`. Cada edición hermana incluye `record_id`, fuente, TITN, título, año, soportes, EAN, ejemplares y URL OPAC.

`EjemplarOut` incluye biblioteca, sucursal, localización, signatura, tipo, soporte y `ubicacion`. `UbicacionOut` tiene código postal, municipio, latitud y longitud opcionales.

### Otras rutas

- `/api/libraries` → `fuente`, `codigo`, `nombre`, `municipio`, `ejemplares`.
- `/api/locations` → `fuente`, `codigo`, `nombre`, `tipo`, biblioteca, municipio y ejemplares.
- `/api/stats` → `ediciones`, `ejemplares`, `bibliotecas`, `por_soporte`.

No tienen parámetros ni manejadores de error propios.

### Salud

`GET /health` ejecuta `SELECT 1` en PostgreSQL y `client.health()` en Meilisearch.

- `database`: `ok` o `error`.
- `meilisearch`: `ok`, `degraded` o `error`.
- `status`: `ok` solo si ambas dependencias están `ok`.
- `version`: versión de la aplicación.

Aunque una dependencia falle, devuelve HTTP 200 con estado degradado. Meilisearch se considera correcto si responde `available` u `ok`.

`GET /` devuelve nombre, versión, `/docs` y `/health`.

## Listas de favoritos

### Persistencia

Modelos compartidos:

- `Lista` → `listas`.
- `ListaItem` → `lista_items`.

`Lista` almacena UUID, SHA-256 del token, título, fechas y expiración. `ListaItem` tiene clave primaria `(lista_id, record_id)`, título snapshot y fecha de adición.

No hay clave foránea de `lista_items.record_id` a `ediciones`. Si una edición desaparece, el elemento permanece con su snapshot.

### Tokens y acceso

`POST /api/lists`:

- Genera `secrets.token_urlsafe(24)`.
- Guarda solo su SHA-256.
- Devuelve el token una sola vez.
- No requiere cuerpo.
- Acepta `X-Client-IP` opcional para el limitador.

No hay cuentas ni roles. El token es una capacidad portadora: quien lo conoce puede leer y editar la lista. Compartir el enlace equivale a compartir permiso de edición.

Un token inválido o caducado devuelve 404 `"Lista no encontrada"`.

### Añadir

`POST /api/lists/{token}/items` acepta:

```json
{"record_id": "madrid:2101557"}
```

o:

```json
{"titn": "2101557"}
```

- Debe existir al menos un campo.
- Si ambos están presentes, `record_id` tiene prioridad.
- Se normaliza la identidad y se comprueba la edición.
- Si ya existe: 200, `saved=true`.
- Si es nuevo y hay menos de 200 elementos: 201.
- Si hay 200 o más: 409.

Errores:

- 404 para lista desconocida/caducada.
- 422 para cuerpo inválido o edición inexistente.
- 409: `"La lista admite como maximo 200 elementos"`.

Puede añadirse una edición marcada con `missing_at`.

### Quitar y renombrar

`DELETE /api/lists/{token}/items/{record_id}`:

- Normaliza la identidad.
- Elimina el elemento si existe.
- Siempre devuelve 200 con `saved=false` y el conteo actual.
- Es idempotente para un elemento ya ausente.

`PATCH /api/lists/{token}` acepta:

```json
{"titulo": "Mi selección"}
```

- Recorta espacios.
- Vacío → `"Mi lista"`.
- Trunca a 80 caracteres.
- El schema acepta hasta 1000 caracteres de entrada.
- `titulo` ausente o `null` restablece el título por defecto.

### Serialización

`ListaItemOut` contiene `record_id`, fuente, TITN, título, soportes, año, póster, URL OPAC y `disponible`.

Si la edición existe:

- Se usan sus metadatos actuales.
- `disponible = missing_at is None`.
- `opac_url` solo se devuelve si está disponible.

Si fue eliminada:

- Se usa `titulo_snapshot`.
- `disponible=false`.
- `opac_url=null`.

`disponible` no significa disponibilidad de préstamo en tiempo real. Los elementos se ordenan por `added_at DESC` y después por `record_id`.

### Caducidad

- TTL: 180 días.
- Máximo: 200 elementos.

Renuevan `updated_at` y `expires_at`:

- Añadir un elemento nuevo.
- Quitar un elemento existente.
- Renombrar.

No renuevan:

- Leer.
- Añadir duplicado.
- Quitar un elemento ausente.

La API no borra listas caducadas; las trata como inexistentes. La limpieza la ejecuta `services/enrich` durante `init` o con `python -m mediateca clean-lists`. Se elimina cualquier lista con `expires_at` vencido, no solo las vacías.

## Middleware y seguridad

### CORS

El único middleware de aplicación es `CORSMiddleware`:

- `allow_origins=settings.cors_origins`.
- `allow_methods=["GET"]`.
- `allow_headers=["*"]`.
- Sin credenciales.

La restricción a GET contrasta con las rutas POST/PATCH/DELETE. El portal actual no se ve afectado porque las Server Actions llaman a la API desde el servidor Next.js.

No hay autenticación, API keys, `TrustedHostMiddleware`, request IDs, límites de cuerpo ni manejador global de excepciones.

### Límite de creación

El limitador de `POST /api/lists` está en memoria:

- 5 creaciones por clave y hora.
- 60 creaciones globales por hora.
- Ventana móvil de una hora.
- Protegido por `threading.Lock`.

Clave:

1. `X-Client-IP`.
2. Primer valor de `X-Forwarded-For`.
3. `"global"`.

Limitaciones:

- Por proceso; no se comparte entre réplicas.
- Se pierde al reiniciar.
- Confía en headers que un cliente directo puede manipular.
- No se aplica a búsquedas, lecturas ni mutaciones.
- No persiste IPs.

### Logs

`TokenMaskFilter` sustituye el segmento posterior a `/api/lists/` por `***` en `uvicorn.access`. También procesa `record.msg` y argumentos tupla/diccionario.

No se aplica automáticamente a proxies ni a tokens presentes en formatos ajenos al patrón de ruta.

### Cookie del portal

La API no usa cookies. El portal recuerda la lista activa con:

- Cookie `mediateca_lista`.
- `HttpOnly`.
- `SameSite=Lax`.
- `Path=/`.
- 180 días.
- `Secure` automático o forzable con `MEDITECA_WEB_COOKIE_SECURE`.

## OpenAPI

`services/api/scripts/export_openapi.py` importa `app`, ejecuta `app.openapi()` y serializa con `ensure_ascii=False` e indentación 2. Por defecto escribe en stdout; acepta una ruta posicional.

```bash
make openapi       # contracts/openapi.json
make web-types     # apps/web/lib/api-types.ts
make contracts     # ambos
```

`make openapi` ejecuta el exportador dentro del contenedor API. `api-types.ts` se genera con `openapi-typescript` y no debe editarse manualmente.

El contrato versionado actual declara `0.7.11`, mientras la aplicación está en `0.8.2`. Debe regenerarse tras cambios de API. El contrato contiene las rutas actuales, pero no documenta todos los estados runtime: por ejemplo, el 201 al añadir un elemento nuevo y los errores 400/404/409/429/503.

## Pruebas y comandos

### Pruebas

Las suites principales son:

- `tests/test_api.py`: búsqueda, filtros, orden, dos pasadas, agregación, fichas, ubicaciones y OpenAPI.
- `tests/test_lists.py`: tokens, idempotencia, snapshots, TTL, límites, renombrado, rate limit y enmascaramiento.

Usan:

- SQLite en memoria con `StaticPool`.
- `Base.metadata.create_all`.
- `app.dependency_overrides` para sesiones e indexadores.
- Fakes de Meilisearch.
- `TestClient(app)` sin entrar en el lifespan.

Por tanto, no requieren PostgreSQL ni Meilisearch reales y no validan el arranque con `check_schema()`.

```bash
make test-api
make test-shared
make test-migrations
make test
make lint
make fmt
```

### Desarrollo local

```bash
python3 -m pip install ./packages/shared
python3 -m pip install -e "./services/api[dev]"
(cd services/api && python -m pytest -q)
(cd services/api && ruff check src tests)
(cd services/api && mypy src)
```

Aunque `pyproject.toml` configura mypy, `make lint` solo ejecuta Ruff.

### Ejecución

```bash
docker compose up -d api
docker compose logs -f api
# o en local
uvicorn mediateca.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Consultas

```bash
curl "http://localhost:8000/api/search?q=abejas&soporte=DVD&soporte=Blu-ray"
curl "http://localhost:8000/api/search?paises_origen=ES&paises_origen=FR&page=1&limit=20"
curl "http://localhost:8000/api/records/madrid:2101557"
curl "http://localhost:8000/api/records/2101557"
curl "http://localhost:8000/api/libraries"
curl "http://localhost:8000/api/locations"
curl "http://localhost:8000/api/stats"
curl "http://localhost:8000/health"
```

## Limitaciones actuales

- El contrato OpenAPI está desactualizado respecto a la versión y a algunos estados HTTP.
- CORS solo autoriza GET.
- El limitador de creación es por proceso y confía en headers de IP.
- No hay fallback de búsqueda a PostgreSQL.
- La agregación posterior a Meilisearch no está dentro del `try` que convierte fallos del índice en 503.
- `add_item()` y `remove_item()` no capturan `RecordIdError`; una identidad con formato inválido puede propagarse como error 500.
- La comprobación del máximo de 200 elementos y la inserción no están protegidas por un lock transaccional.
- `MEDIATECA_OPAC_BASE_URL` y `MEDIATECA_OPAC_PATH` no controlan los enlaces devueltos por la API.
- Las pruebas no entran en el lifespan y no validan el arranque contra un esquema real.

## Documentación relacionada

- [Modelos y esquemas compartidos](../../packages/shared/README.md)
- [Ingesta y migraciones](../../services/enrich/README.md)
- [Portal](../../apps/web/README.md)
- [Operación y despliegue](../../docs/OPERATIONS.md)
- [Arquitectura](../../docs/ARCHITECTURE.md)
