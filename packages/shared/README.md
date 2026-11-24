# Mediateca Madrid — modelos y contratos compartidos

`mediateca-shared` es la fuente común de modelos SQLAlchemy 2, esquemas Pydantic 2, constantes de estado y utilidades puras utilizadas por la API y la ingesta.

No contiene engines, sesiones, configuración de entorno, clientes OPAC/TMDB/Meilisearch ni lógica de migración. Es una biblioteca de definiciones y transformaciones; los efectos externos pertenecen a `services/api` y `services/enrich`.

## Índice

- [Alcance y consumo](#alcance-y-consumo)
- [Estructura y empaquetado](#estructura-y-empaquetado)
- [`Base` y registro de modelos](#base-y-registro-de-modelos)
- [Modelos del catálogo](#modelos-del-catálogo)
- [Cola, ejecuciones y metadatos](#cola-ejecuciones-y-metadatos)
- [Listas](#listas)
- [Estados y constantes](#estados-y-constantes)
- [Identidad](#identidad)
- [Títulos](#títulos)
- [Soportes audiovisuales](#soportes-audiovisuales)
- [Perfiles de fuente](#perfiles-de-fuente)
- [Esquemas Pydantic](#esquemas-pydantic)
- [`SCHEMA_VERSION` y migraciones](#schema_version-y-migraciones)
- [Reglas de extensión](#reglas-de-extensión)
- [Pruebas y comandos](#pruebas-y-comandos)

## Alcance y consumo

| Contenido | Consumidores |
|---|---|
| Modelos SQLAlchemy | API e ingesta |
| Esquemas Pydantic | API y generación OpenAPI |
| `SCHEMA_VERSION` | API al arrancar e ingesta al migrar |
| Identidad, títulos y soportes | API, ingesta, indexador y TMDB |
| `FuenteProfile` | API, OPAC y directorio de bibliotecas |
| Constantes de trabajos/estados | Worker, scheduler y dashboard |

Versiones distintas:

- `__version__ = "0.8.2"`: versión de distribución del paquete.
- `SCHEMA_VERSION = "8"`: versión del esquema PostgreSQL.

`make bump` actualiza la primera, no la segunda.

### Propiedad de escrituras

- `services/enrich`: migraciones, `schema_meta`, catálogo, cola, configuración e índice.
- `services/api`: lectura del catálogo e índice; escritura solo de listas.
- `apps/web`: no importa Python ni accede a almacenamientos; consume la API.
- `packages/shared`: no escribe nada.

## Estructura y empaquetado

```text
packages/shared/
├── src/mediateca_shared/
│   ├── __init__.py          # __version__ y SCHEMA_VERSION
│   ├── db.py                # Base declarativa
│   ├── models.py            # catálogo, cola, carreras y SchemaMeta
│   ├── lists.py             # Lista y ListaItem
│   ├── schemas.py           # contratos Pydantic
│   ├── constants.py         # trabajos, estados y conflictos
│   ├── version.py           # SCHEMA_VERSION y validación
│   ├── identity.py          # fuentes, TITN, record_id y ubicaciones
│   ├── titles.py            # normalización de títulos
│   ├── soportes.py          # clasificación audiovisual
│   └── fuentes.py           # FuenteProfile y URLs OPAC
├── tests/
│   ├── test_schema.py
│   ├── test_lists.py
│   ├── test_identity.py
│   ├── test_soportes.py
│   └── test_titles.py
└── pyproject.toml
```

Metadatos:

- Nombre: `mediateca-shared`.
- Python: `>=3.11,<3.15`.
- Dependencias runtime: `sqlalchemy>=2.0.36`, `pydantic>=2.10`.
- Desarrollo: `pytest>=8.3`, `ruff>=0.8`.
- Build backend: Hatchling.
- Wheel: `src/mediateca_shared`.
- Ruff: línea 100, `py311`, reglas `E`, `F`, `I`, `UP`, `B`.

No hay scripts de consola, recursos de datos ni OpenAPI dentro del paquete.

### Instalación local

Desde la raíz:

```bash
python -m pip install ./packages/shared
```

Para desarrollo editable:

```bash
cd packages/shared
python -m pip install -e ".[dev]"
pytest -q
ruff check src tests
ruff format --check src tests
```

API e ingesta no declaran `mediateca-shared` como dependencia publicada. Sus Dockerfiles instalan el paquete desde la ruta local:

- `batch.Dockerfile`: `pip install /app/packages/shared`.
- `web.Dockerfile`: instalación no editable en `/opt/venv`.

“No se publican wheels versionados” significa que no se mantienen artefactos vendorizados ni se sincronizan entre repositorios. `pip install` de una ruta local puede construir un wheel transitorio.

Ambas imágenes deben reconstruirse desde el mismo commit. No hay un workspace Python raíz ni un lockfile Python.

## `Base` y registro de modelos

`db.py` define únicamente:

```python
class Base(DeclarativeBase):
    ...
```

Importar `Base` no descubre automáticamente todos los modelos. Para que `Base.metadata.create_all()` los vea hay que importar los módulos que los declaran.

`models.py` importa al final `Lista` y `ListaItem` para registrarlos. La ingesta además importa su modelo local `AppConfig`, que usa la misma `Base` pero no pertenece a shared.

### Defaults

- `default=` actúa normalmente en el cliente/ORM.
- `server_default=` se emite también en el DDL.
- `onupdate=func.now()` de SQLAlchemy no crea un trigger PostgreSQL.
- Las migraciones añaden algunos `server_default` que no existen como tales en el modelo.

Una escritura SQL cruda no recibe necesariamente todos los defaults Python.

## Modelos del catálogo

Fuente: [`src/mediateca_shared/models.py`](src/mediateca_shared/models.py).

Las anotaciones no opcionales implican columnas no nulas. Las fechas usan `DateTime(timezone=True)`.

### `Fuente` → `fuentes`

Campos:

- Identidad: `id`, `codigo`, `nombre`.
- Adaptador: `adapter`, `base_url`, `opac_path`.
- Sesión: `session_pattern`, `format_field`, `format_value`.
- Operación: `enabled`, `delay`, `captcha_policy`, `paused_until`.
- Configuración: `options` JSON.
- Auditoría: `created_at`, `updated_at`.

Defaults:

- `adapter="absysnet"`.
- `opac_path=""`.
- `session_pattern="/abnetopac/([A-Za-z0-9]+)"`.
- `format_field="select03"`.
- `format_value="6"`.
- `enabled=True`.
- `delay=1.0`.
- `captcha_policy="pause"`.
- `options={}`.

Restricciones e índices:

- `uq_fuentes_codigo` sobre `codigo`.
- `ix_fuentes_codigo`.
- `ix_fuentes_enabled`.

Relaciones: `ediciones`, `bibliotecas`, `sucursales`, `ejemplares` y `jobs`. Las FK hijas usan `ON DELETE RESTRICT`.

`Fuente._validate_codigo()` exige `^[a-z0-9][a-z0-9-]*$`. Es validación Python; no hay un `CHECK` SQL equivalente.

### `Obra` → `obras`

Representa una obra global que puede agrupar ediciones de fuentes distintas.

Campos: `id`, `titulo_uniforme`, `anio`, `director_principal`, `manual`, `created_at`, `updated_at`.

- `uq_obra_titulo_anio` sobre `(titulo_uniforme, anio)`.
- Índices por título y año.
- Relación `ediciones`.

En PostgreSQL, `UNIQUE` con `anio NULL` permite múltiples filas del mismo título y año nulo. La aplicación consulta explícitamente `anio IS NULL` para reutilizar la obra.

### `Edicion` → `ediciones`

Registro bibliográfico identificado globalmente por `record_id`.

#### Identidad y agrupación

- `id`, `fuente_id`, `record_id`, `titn`.
- `obra_id` opcional.
- `obra_manual`, `obra_manual_at`.

#### Bibliografía

- `titulo`, `titulo_uniforme`, `publicacion`, `anio`.
- `idioma`, `pais`, `ean`, `tipo_documento`.
- `duracion_min`, `edad_recomendada`, `sinopsis`.
- `notas` y `marc` JSON.
- `soportes`, `soporte_principal`, `generos`.

#### TMDB

- `paises_origen`, default `[]`.
- `tmdb_id`, `tmdb_poster_url`, `tmdb_url`, `tmdb_enriched_at`.

#### Estado OPAC

- `enrich_status`, default `"pending"`.
- `enrich_attempts`, default `0`.
- `enrich_last_attempt_at`, `enrich_last_error`.

#### Estado TMDB

- `tmdb_status`, default `"pending"`.
- `tmdb_attempts`, default `0`.
- `tmdb_last_attempt_at`, `tmdb_last_error`.

#### Procedencia y progreso

- `source_url`, `is_stub`, `discovery_seen_at`.
- `detail_fetched_at`, `missing_at`.
- `created_at`, `updated_at`.

Restricciones:

- `uq_ediciones_fuente_titn` sobre `(fuente_id, titn)`.
- `uq_ediciones_record_id` sobre `record_id`.
- FK de fuente con `RESTRICT`.
- FK de obra con `CASCADE`.

Índices:

- Fuente, TITN, obra, año, idioma y país.
- `tmdb_enriched_at`.
- `enrich_status`, `tmdb_status`.
- `soporte_principal`, EAN, `is_stub`.
- `discovery_seen_at`, `detail_fetched_at`.
- Compuestos `(enrich_status, titn)` y `(tmdb_status, titn)`.

No hay índice sobre `missing_at`.

Relaciones con cascada `all, delete-orphan`: `ejemplares`, `personas`, `materias` y `enlaces`.

Caveats de integridad:

- La base no comprueba que `record_id` coincida con el código de fuente y el TITN.
- Los estados son cadenas libres, no enums SQL.
- `Obra.ediciones` no declara cascada ORM, aunque la FK SQL de `obra_id` usa `CASCADE`.

### `Biblioteca` → `bibliotecas`

Campos: `id`, `fuente_id`, `codigo`, `nombre`, `municipio`, `direccion`, `codigo_postal`, `latitud`, `longitud`.

- Unicidad por `(fuente_id, codigo)`.
- FK de fuente con `RESTRICT`.
- Índices por fuente, código, nombre y municipio.
- Relaciones `fuente`, `ejemplares` y `sucursales`; estas últimas con cascada ORM.
- No tiene timestamps.

### `Sucursal` → `sucursales`

Campos: `id`, `fuente_id`, `biblioteca_id`, `codigo`, `nombre`, `municipio`, `direccion`, `codigo_postal`, `latitud`, `longitud`, `updated_at`.

- Unicidad por `(fuente_id, codigo)`.
- FK de fuente con `RESTRICT`.
- FK de biblioteca con `CASCADE`.
- Índices por fuente, biblioteca, código, municipio y código postal.

No existe una restricción SQL que garantice que biblioteca y sucursal tengan el mismo `fuente_id`.

### `Ejemplar` → `ejemplares`

Campos: `id`, `fuente_id`, `edicion_id`, `biblioteca_id`, `external_key`, `sucursal_codigo`, `sucursal_nombre`, `localizacion`, `signatura`, `tipo_ejemplar`, `soporte`, `updated_at`.

- Unicidad por `(fuente_id, external_key)`.
- FK de fuente, edición y biblioteca con `RESTRICT`, `CASCADE` y `CASCADE`.
- Índices por fuente, edición, biblioteca, `external_key`, sucursal, signatura y soporte.

Relaciones:

- `fuente`, `edicion`, `biblioteca`.
- `sucursal` es `viewonly=True`, `uselist=False`, sin FK real; se resuelve por `(fuente_id, sucursal_codigo)`.

Caveats:

- Un código de sucursal ausente simplemente no resuelve la relación.
- No se garantiza por SQL que edición, ejemplar y biblioteca pertenezcan a la misma fuente.
- No se almacena estado de préstamo.
- El productor calcula `external_key`; el modelo no lo calcula.
- La reingesta actualiza ejemplares reconocidos, pero no elimina los que dejan de aparecer.

### `Persona` y `EdicionPersona`

`Persona`:

- Tabla `personas`.
- `id`, `nombre`, `nombre_normalizado`.
- `nombre_normalizado` único e indexado.
- Relación `ediciones` hacia las asociaciones.

`EdicionPersona`:

- Tabla `edicion_persona`.
- `id`, `edicion_id`, `persona_id`, `rol`, `orden`.
- Único por `(edicion_id, persona_id, rol)`.
- FK con `CASCADE`.
- Índices por edición, persona y rol.
- `orden` default `0`.

La normalización del nombre se hace en el repositorio de ingesta; la base solo garantiza unicidad del resultado.

### `Materia` y `EdicionMateria`

`Materia`:

- Tabla `materias`.
- `id`, `termino`.
- `termino` único e indexado.

`EdicionMateria`:

- Tabla `edicion_materia`.
- `id`, `edicion_id`, `materia_id`.
- Único por `(edicion_id, materia_id)`.
- FK con `CASCADE`.

La búsqueda en ingesta usa `lower(termino)`, pero la restricción única es sobre el texto exacto. No hay índice único funcional sobre `lower(termino)`.

### `Enlace`

- Tabla `enlaces`.
- `id`, `edicion_id`, `url`, `etiqueta`.
- FK de edición con `CASCADE`.
- Índice por edición.
- No hay unicidad de URL.

## Cola, ejecuciones y metadatos

### `HarvestJob` → `harvest_jobs`

Campos:

- `id`, `fuente_id` opcional.
- `job_type`, `status`.
- `cursor_doc`, `cursor_titn`.
- `batch_size`, `attempts`, `max_attempts`.
- `stats` JSON, `error`.
- `created_at`, `started_at`, `finished_at`, `heartbeat_at`.

Defaults: `status="pending"`, `batch_size=5000`, `attempts=0`, `max_attempts=3`, `stats={}`.

- FK opcional de fuente con `RESTRICT`.
- Los trabajos `index` globales pueden tener `fuente_id NULL`.
- Índices por fuente, tipo, estado, `(status, job_type)` y `(fuente_id, status)`.
- Propiedades calculadas `fuente_codigo` y `fuente_nombre`.

No hay restricciones SQL para tipos o estados.

### `HarvestRun` → `harvest_runs`

Campos: `id`, `kind`, `query`, `started_at`, `finished_at`, `status`, `stats`, `error`.

- `status` default `"running"`.
- Índice por `kind`.
- No tiene relación con `Fuente`; el código puede estar dentro de `stats`.
- La ingesta escribe `"finished"`, no `"completed"`.

### `SchemaMeta` → `schema_meta`

Tabla clave/valor:

- `key` String(64), clave primaria.
- `value` String(64), no nulo.

No conserva historial de migraciones. La clave utilizada es `schema_version`.

## Listas

Fuente: [`src/mediateca_shared/lists.py`](src/mediateca_shared/lists.py).

### `Lista` → `listas`

- `id` UUID, default Python `uuid.uuid4`.
- `token_hash` String(64), único e indexado.
- `titulo` String(80), default `"Mi lista"`.
- `created_at`, `updated_at`, `expires_at`.
- Índice `ix_listas_expires_at`.
- Relación `items` con cascada ORM y orden `added_at DESC`.

### `ListaItem` → `lista_items`

- Clave primaria `(lista_id, record_id)`.
- FK de lista con `CASCADE`.
- `titulo_snapshot`.
- `added_at`.
- Índice `(lista_id, added_at)`.

No hay FK de `record_id` a `Edicion`. Si la edición desaparece, el elemento permanece y se usa el snapshot. No hay columna `fuente`; se deriva de `record_id`.

El token opaco no se guarda, solo su SHA-256.

## Estados y constantes

Fuente: [`src/mediateca_shared/constants.py`](src/mediateca_shared/constants.py). Son tuplas de cadenas, no enums de Python ni SQL.

### Trabajos

```python
JOB_TYPES = ("discover", "enrich", "index", "tmdb", "branches")
JOB_STATUSES = ("pending", "running", "completed", "failed", "cancelled")
FINAL_STATUSES = ("completed", "failed", "cancelled")
```

- `DEFAULT_BATCH_SIZE=5000`.
- `DEFAULT_MAX_ATTEMPTS=3`.
- Concurrencia mínima 1 y máxima 5.

Conflictos:

```python
JOB_CONFLICT_PAIRS = (
    ("discover", "enrich"),
    ("enrich", "tmdb"),
    ("enrich", "index"),
    ("tmdb", "index"),
)
```

Cada tipo también conflicta consigo mismo. `branches` es compatible con todos. La exclusión se implementa en aplicación y se serializa con `pg_advisory_xact_lock`; no es una restricción de la tabla.

Transiciones observadas:

- Creación → `pending`.
- Reclamo → `running`.
- Éxito → `completed`.
- Fallo agotado → `failed`.
- Reintento → `pending`.
- CAPTCHA → reencola sin consumir intento y pausa la fuente.
- Heartbeat caducado → reencola o falla según `max_attempts`.
- `cancelled` está admitido por `finish_job`, pero no se observó un escritor normal de producción.

### Enriquecimiento OPAC

```python
ENRICH_STATUSES = ("pending", "enriched", "failed")
```

- Éxito: `enriched`, incrementa intentos, fecha y limpia error.
- Fallo: `failed`, incrementa intentos y guarda error.
- Material no audiovisual: `mark_non_audiovisual()` escribe `"skipped"`, fija `detail_fetched_at` y `missing_at`, y no incrementa intentos.

`"skipped"` no está en `ENRICH_STATUSES`. Los filtros basados en la constante no lo ofrecen, aunque las consultas de resumen pueden agregar valores desconocidos.

### TMDB

```python
TMDB_STATUSES = ("pending", "matched", "unmatched", "error", "skipped")
```

- Sin token: `skipped`, sin incremento de intentos ni fecha de intento.
- `matched`, `unmatched`, `error`: incrementan intentos y guardan fecha/error.
- `pais` pertenece al OPAC y no se sobrescribe.
- `paises_origen` procede de TMDB y usa códigos ISO de dos letras en mayúsculas.

### Otros estados

- `HarvestRun`: `running`, `finished`, `failed`.
- `ListaItemOut.disponible`: no significa disponibilidad de préstamo; se calcula como `Edicion.missing_at is None`.
- `Fuente.adapter`, `Fuente.captcha_policy` y roles de persona son cadenas libres.

## Identidad

Fuente: [`src/mediateca_shared/identity.py`](src/mediateca_shared/identity.py).

Símbolos principales:

- `MADRID="madrid"`.
- `FUENTE_CODIGO_RE`, `TITN_RE`, `RecordIdError`.
- `validate_fuente_codigo()`, `validate_titn()`.
- `compose_record_id()`, `parse_record_id()`, `normalize_record_id()`.
- `record_id_fuente()`, `record_id_titn()`.
- `normalize_location_code()`.

Contrato:

- Fuente: `^[a-z0-9][a-z0-9-]*$`.
- TITN: máximo 32 y `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
- Identidad canónica: `<fuente>:<titn>`.
- Un TITN sin fuente se interpreta como Madrid.
- `parse_record_id()` recorta espacios externos y exige exactamente un `:` cuando está presente.

`normalize_location_code()`:

- `b:RBMALC` → `b:madrid:RBMALC`.
- `s:BMALC1` → `s:madrid:BMALC1`.
- Los códigos ya cualificados se mantienen.
- Los nombres de biblioteca se devuelven sin cambios.

## Títulos

Fuente: [`src/mediateca_shared/titles.py`](src/mediateca_shared/titles.py).

### `clean_title()`

- Normaliza a NFC.
- Convierte NBSP a espacio.
- Neutraliza separadores invisibles y caracteres de control.
- Colapsa whitespace.
- Elimina puntuación ISBD final `/ : ; , . =`.
- Conserva `?`, `!`, corchetes y paréntesis.
- Devuelve `None` si queda vacío.

### `split_responsibility()`

Divide antes de una mención de responsabilidad introducida por `/` precedido de whitespace. No divide `AC/DC`.

### `strip_form_qualifier()`

Elimina calificadores finales como `(Película cinematográfica)`, `(Documental)` o `(Serie)`, incluso si hay varios. Conserva `(2020)` y `(versión del director)`.

### `strip_material_qualifier()`

Reconoce grupos como `[DVD-Vídeo]`, `(Blu-ray)`, `[VHS]` o `[Archivo de ordenador]`.

- Usa tokenización NFKD sin diacríticos.
- Conserva grupos que forman parte del título, como `[Rec]` o `[tercera temporada]`.
- Corrige corchetes cuadrados desbalanceados.

`has_balanced_brackets()` solo compara cantidades de `[` y `]`; no valida anidamiento ni orden.

### `strip_all_brackets()`

Elimina todos los grupos simples entre corchetes o paréntesis. Se usa solo para generar candidatos TMDB; nunca debe usarse para persistir el título definitivo.

## Soportes audiovisuales

Fuente: [`src/mediateca_shared/soportes.py`](src/mediateca_shared/soportes.py).

```python
SUPPORT_ORDER = ["4K UHD", "Blu-ray", "DVD", "VHS"]
```

### `detect_soportes()`

Acepta descripción física, soportes de ejemplares y tipo de documento.

- Puede devolver varios formatos.
- Elimina duplicados y ordena por `SUPPORT_ORDER`.
- Excluye DVD-ROM, CD-ROM, CD-DA y audio genérico.
- Reconoce variantes andaluzas como videodisco, disco óptico, CD-Video y casete.
- Aplica heurísticas para resolver contradicciones.

### `detect_audiovisual()`

Devuelve:

- `True`: hay soporte o pista audiovisual.
- `False`: hay información suficiente y no es audiovisual.
- `None`: no hay datos suficientes.

Diapositivas y transparencias se consideran no audiovisuales salvo que exista una pista audiovisual explícita.

### Otras funciones

- `canonical_soporte()`: primer soporte detectado o texto original limpio.
- `soporte_principal()`: un soporte → ese valor; varios → `"Varios"`; vacío → `None`.
- `normalize_text()`: normalización compartida.

## Perfiles de fuente

Fuente: [`src/mediateca_shared/fuentes.py`](src/mediateca_shared/fuentes.py).

`FuenteProfile` es un dataclass `frozen=True`, `slots=True`, que repite los campos operativos de `Fuente`.

- `from_model()` copia los valores del modelo y hace una copia superficial de `options`.
- `opac_url` concatena `base_url.rstrip("/") + opac_path`.
- `source_url(titn)` genera `opac_url + "?TITN=" + titn`.

`MADRID_PROFILE` contiene un perfil estático Madrid. La función `source_url(profile, titn)` usa Madrid si `profile` es `None`.

Caveats:

- `MADRID_PROFILE` no lee entorno ni la tabla `fuentes`.
- `opac_url` asume que `opac_path` incluye la barra inicial.
- La API recalcula `source_url` desde el perfil; no devuelve necesariamente `Edicion.source_url`.
- `options` no tiene esquema de validación. Los consumidores interpretan claves como `discovery`, `coverage`, `detail_on_discovery`, `verify_tls`, `directory`, `subcat`, `select05` y `search_extra`.

## Esquemas Pydantic

Fuente: [`src/mediateca_shared/schemas.py`](src/mediateca_shared/schemas.py).

Son contratos de API, no una representación completa de los modelos ORM. No usan `strict=True`.

### Salud y búsqueda

#### `HealthResponse`

Obligatorios: `status`, `database`, `meilisearch`, `version`. `version` es la versión de la aplicación, no `SCHEMA_VERSION`.

#### `SearchHitFormatted`

- `titulo: str | None`.
- `sinopsis: str | None`.
- `extra="allow"`.

#### `SearchHit`

Obligatorios: `id`, `titn`, `titulo`.

Opcionales/default:

- `record_id`, `fuente`, `fuente_nombre`.
- `obra_id`, `obra_titulo`, `ediciones_count=1`.
- `titulo_uniforme`, `publicacion`, `anio`, `idioma`, `pais`.
- `paises_origen=[]`.
- `tmdb_poster_url`, `tmdb_url`.
- `duracion_min`, `edad_recomendada`, `sinopsis`.
- `generos=[]`, `materias=[]`, `soportes=[]`.
- `soporte_principal`.
- `bibliotecas=[]`, `ejemplares=0`.
- `directores=[]`, `actores=[]`, `guionistas=[]`.
- `formatted`, serializado como `_formatted`.

Configuración: `populate_by_name=True`; los campos adicionales del documento se ignoran por defecto. `id` es el ID de Meilisearch, no `Edicion.id`.

#### `SearchResponse`

Obligatorios: `query`, `page`, `limit`, `total`, `total_pages`, `took_ms`, `facets`, `hits`. Default: `total_ediciones=0`.

Semántica:

- `total` cuenta obras/grupos por `distinct="obra_key"`.
- `total_ediciones` cuenta ediciones sin agrupar.
- La API agrega soportes, bibliotecas, ejemplares y metadatos de todas las ediciones de la obra.

### Fichas

| Esquema | Contenido |
|---|---|
| `PersonaOut` | `nombre`, `rol` |
| `EnlaceOut` | `url`, `etiqueta` |
| `UbicacionOut` | CP, municipio, latitud, longitud |
| `EjemplarOut` | Biblioteca, sucursal, localización, signatura, tipo, soporte, ubicación |
| `ObraEdicionOut` | Identidad, fuente, título, año, soportes, EAN, ejemplares, URL |
| `ObraOut` | ID, título uniforme, año, director, ediciones |
| `RecordDetail` | Identidad, bibliografía, TMDB, contenido, relaciones, obra, notas, MARC, URL y actualización |

`RecordDetail` no expone estados internos, contadores, `is_stub`, marcas de progreso ni campos de agrupación manual. `notas` es `dict[str, str]`, más estrecho que el modelo ORM `dict[str, Any]`.

### Bibliotecas y estadísticas

- `LibraryOut`: fuente, código, nombre, municipio, ejemplares.
- `LocationOut`: fuente, código, nombre, tipo, biblioteca, municipio, ejemplares.
- `StatsResponse`: ediciones, ejemplares, bibliotecas y `por_soporte`.

### Listas

| Esquema | Contenido |
|---|---|
| `ListaItemOut` | Identidad, fuente, título, soportes, año, póster, OPAC, disponible |
| `ListaOut` | Título, conteo, fechas e items |
| `ListaCreatedOut` | Solo `token` |
| `ListaItemIn` | `record_id` o `titn`; al menos uno |
| `ListaRenameIn` | `titulo` opcional, máximo 1000 |
| `ItemMutationOut` | `item_count`, `saved` |

`ListaItemIn.identity` prioriza `record_id`. No valida el regex de TITN ni coherencia entre ambos campos. La API recorta el renombrado a 80 caracteres para ajustarse a `Lista.titulo`.

### Generación del contrato

La API reexporta estos esquemas desde `services/api/src/mediateca/api/schemas.py`.

```bash
make openapi
make web-types
make contracts
```

El portal no importa Python; consume `contracts/openapi.json` y los tipos TypeScript generados.

## `SCHEMA_VERSION` y migraciones

Fuente: [`src/mediateca_shared/version.py`](src/mediateca_shared/version.py).

```python
SCHEMA_VERSION = "8"
```

`check_schema_version(value)` exige igualdad exacta con `"8"`. `None` o cualquier otro valor lanza `SchemaVersionError`. No compara versiones semánticas ni convierte a entero.

### API

- Consulta `SchemaMeta`.
- Ejecuta `check_schema()` en el lifespan antes de aceptar tráfico.
- No crea tablas, no migra y no escribe `schema_meta`.
- Si falta la tabla o la versión no coincide, el arranque falla.

### Ingesta

`_apply_migrations()`:

1. Busca `scripts/migrate_*.sql`.
2. Los ordena alfabéticamente.
3. Crea antes `Fuente` y siembra Madrid.
4. Ejecuta todos los scripts en una transacción.
5. Sobrescribe al final el valor de `schema_meta` con `key='schema_version'` por `SCHEMA_VERSION`.

`migrate` solo aplica SQL. `init` crea el esquema, aplica migraciones, limpia listas e indexa; usa `reset=True` si no había versión o si la anterior era numéricamente menor.

No hay Alembic ni historial de migraciones. Todos los scripts se reejecutan en cada invocación.

### Inventario

| Migración | Efecto principal | Versión escrita |
|---|---|---:|
| `migrate_ingesta.sql` | Cola, progreso y retirada de snapshots | 1 |
| `migrate_tmdb.sql` | Países, IDs, URLs y sincronización TMDB | 3 |
| `migrate_enriquecimiento_estado.sql` | Estados e intentos OPAC/TMDB | 4 |
| `migrate_sucursales_geo.sql` | Sucursales y CP de biblioteca | 5 |
| `migrate_listas.sql` | Listas y elementos | 6 |
| `migrate_fuentes.sql` | Fuentes, identidad compuesta y listas | 7 |
| `migrate_agrupacion_manual.sql` | Agrupación manual | 8 |
| `migrate_disponibilidad.sql` | Retira datos de préstamo | — |
| `migrate_flaresolverr.sql` | `app_config` | — |
| `migrate_andalucia.sql` | Siembra Andalucía | — |
| `migrate_andalucia_directory.sql` | Directorio abierto andaluz | — |
| `migrate_fuentes_autonomicas.sql` | Diez fuentes autonómicas | — |
| `migrate_fuentes_cobertura.sql` | Cinco fuentes CCBIP | — |

No existe una migración numerada 2.

### Orden alfabético

El orden no es cronológico. Una migración puede escribir una versión menor después de una mayor; al terminar la transacción, CLI restaura el valor final `8`. Ejecutar scripts individualmente puede dejar valores intermedios inesperados.

### `create_all` y migraciones

- `create_all()` crea tablas ausentes; no altera tablas existentes.
- Las migraciones son necesarias para instalaciones históricas.
- `create_all()` no inserta `schema_version`.
- El DDL de SQLAlchemy y las migraciones no son idénticos en todos los defaults e índices.
- `onupdate` no genera triggers.

### Backfill de fuentes

`migrate_fuentes.sql`:

- Siembra Madrid.
- Asigna fuente a ediciones, bibliotecas, sucursales, ejemplares y trabajos históricos.
- Genera `record_id='madrid:' || titn`.
- Mantiene `fuente_id NULL` para indexados globales.
- Sustituye unicidades globales por unicidades compuestas.
- Convierte `lista_items` de TITN a `record_id`.

Tras los seeds existen 17 fuentes: Madrid y Andalucía habilitadas, diez autonómicas deshabilitadas y cinco CCBIP deshabilitadas.

### Meilisearch

La clave primaria real es `id`, derivado de `record_id`. El documento también conserva `record_id`.

- `obra_key="obra:<id>"` si hay obra.
- `obra_key="edicion:<record_id>"` si no la hay.
- `index` sin reset añade/actualiza y no elimina huérfanos.
- `index --reset` vacía y reconstruye.

### Diferencias de despliegue

Compose ejecuta `python -m mediateca init` y aplica el reset condicional.

Portainer ejecuta por separado `init-db`, `migrate`, `clean-lists` e `index`. No usa el comando unificado ni `index --reset`; una migración de identidad o agrupación puede requerir un reindexado completo manual.

Otros caveats:

- `make migrate` sobre una base totalmente vacía no es un bootstrap completo.
- Si `schema_meta` contiene un valor no numérico, `init` puede fallar al calcular el reset.
- No hay protección explícita contra desplegar una versión de paquete inferior a la registrada.
- Dos imágenes de commits distintos con el mismo `SCHEMA_VERSION` pueden superar la comprobación de arranque.

## Reglas de extensión

### Cambios de modelo

1. Editar `models.py` o `lists.py`.
2. Declarar tipos, nullabilidad, defaults, FK, índices y cascadas.
3. Registrar cualquier módulo nuevo de modelos antes de `create_all()`.
4. No añadir engines, sesiones ni configuración a shared.

### Migraciones

1. Añadir SQL idempotente en `services/enrich/scripts` en el mismo commit.
2. Incluir backfill y defaults de servidor cuando corresponda.
3. No confiar en `create_all()` para modificar tablas existentes.
4. Ejecutar `make test-migrations`.

### Versión del esquema

- Incrementar `SCHEMA_VERSION` ante cambios incompatibles de PostgreSQL.
- No incrementarlo por simples seeds o cambios que solo exigen reindexar.
- No confundirlo con `__version__`.

### Estados

- Actualizar constantes, escritores, lectores, filtros y pruebas.
- Evitar valores no representados, como el `enrich_status="skipped"` actual.

### Contratos API

- Añadir campos opcionales o con default para preservar clientes.
- Actualizar serializadores y agregación.
- Regenerar OpenAPI y TypeScript con `make contracts`.

### Índice

- Los cambios de documentos y settings pertenecen a `services/enrich/src/mediateca/catalog/indexer.py`.
- Identidad, agrupación o `obra_key` cambiantes exigen reconstrucción completa.
- Un cambio solo del índice no implica necesariamente subir `SCHEMA_VERSION`.

### Pruebas mínimas

```bash
make test-shared
make test-api
make test-enrich
make test-migrations
make lint
make contracts
```

## Pruebas y comandos

### Cobertura de shared

- `test_schema.py`: modelos en SQLite, versión, campos TMDB/estado, sucursales, agrupación y defaults de esquemas.
- `test_lists.py`: registro de tablas, título por defecto, clave compuesta y cascada.
- `test_identity.py`: composición, parseo, TITN suelto y códigos históricos.
- `test_soportes.py`: formatos, exclusiones, variantes andaluzas y clasificación triestado.
- `test_titles.py`: puntuación, responsabilidad, calificadores y corchetes.

### Pruebas de consumidores

- API: filtros, identidad, ubicación, agregación, listas y OpenAPI.
- Ingesta: upserts, obras manuales, mismas fuentes, indexador, estados, cola y migraciones.

### Comandos canónicos

```bash
make test-shared
make test-api
make test-enrich
make test
make test-migrations
make lint
make fmt
make check-schema
make build
make init
make migrate
make index-reset
make contracts
```

La vía soportada para ejecutar las suites del monorepo es mediante los contenedores definidos en el `Makefile`.

## Documentación relacionada

- [API](../../services/api/README.md)
- [Ingesta y migraciones](../../services/enrich/README.md)
- [Portal](../../apps/web/README.md)
- [Arquitectura](../../docs/ARCHITECTURE.md)
- [Operación y despliegue](../../docs/OPERATIONS.md)
