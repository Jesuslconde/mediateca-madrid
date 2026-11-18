# Design

## Context

Ver `proposal.md` para la motivación. El estado actual relevante:

- `Edicion.titn`, `Biblioteca.codigo` y `Sucursal.codigo` son únicos globalmente. `TITN` colisiona entre catálogos: el 48 existe en Madrid y en Andalucía con títulos distintos.
- El índice usa `id = titn`; la API expone `/api/records/{titn}`; las listas guardan `titn` como clave; el portal enlaza `/registro/{titn}`.
- Los trabajos se identifican por tipo, sin fuente. `coverage`, `select_pending_titns`, `mark_absent_since` y `index_titns` operan sobre todo el catálogo.
- El cliente OPAC, la sesión, el filtro `select03` y el enlace permanente están cableados a Madrid. AbsysNet comparte estructura HTML entre Madrid y Andalucía, pero no ruta, sesión ni valores de formulario.
- La ingesta es la única propietaria de migraciones y escrituras del catálogo; la API solo lee catálogo y escribe listas. `SCHEMA_VERSION` actual: `6`.

## Goals / Non-Goals

**Goals:**

- Introducir la fuente como dimensión transversal con Madrid como única fuente activa.
- Conservar el comportamiento y las URLs de Madrid, incluidas las listas y los enlaces compartidos.
- Dejar el modelo, los trabajos, el índice, la API y el portal listos para una segunda fuente sin otra migración de identidad.
- Entregar una migración idempotente y un procedimiento de reindexado verificable.

**Non-Goals:**

- Añadir datos o perfiles operativos de Andalucía; eso corresponde a `ingesta-andalucia`.
- Unificar ediciones de la misma película entre fuentes o cambiar la búsqueda a resultados por obra.
- Directorio andaluz, direcciones, códigos postales nacionales o cercanía fuera de Madrid.
- Cambiar el branding o el nombre del producto.
- Introducir adaptadores de OPAC que no sean AbsysNet.

## Decisions

### D1. Registro de fuentes: tabla persistente y adaptador en código

Se crea una tabla `fuentes` con `codigo` estable e inmutable, `nombre`, `adapter` (`absysnet`), `base_url`, `opac_path`, campos comunes de perfil (`session_pattern`, `format_field`, `format_value`), `enabled`, `delay`, `captcha_policy` y un `options` JSON para lo específico de cada adaptador. La migración siembra `madrid` con los valores actuales de `MEDIATECA_OPAC_BASE_URL` y `MEDIATECA_OPAC_PATH`.

El perfil operativo vive en la base para poder habilitar o deshabilitar una fuente, cambiar su retardo o su URL sin reconstruir la imagen. El comportamiento del adaptador y del parser vive en código.

Alternativas descartadas:

- Solo variables de entorno: no permite habilitar fuentes en caliente ni guardar estado por fuente; el dashboard no puede operarlas.
- Solo un fichero YAML: misma limitación operativa y obliga a reconstruir para cambiar una URL.

`Fuente.codigo` se valida con `^[a-z0-9][a-z0-9-]*$` y no se renombra: forma parte de `record_id` y de las URLs.

### D2. Identidad: `record_id` persistido y unicidad compuesta

`Edicion` gana `fuente_id` y `record_id` (`<fuente>:<titn>`), con `UNIQUE (fuente_id, titn)` y `UNIQUE (record_id)`. `record_id` se calcula al crear o actualizar la edición y no se recalcula en cada enriquecimiento.

Se persiste `record_id` en lugar de calcularlo siempre por `JOIN` porque:

- las listas y la API lo necesitan como clave estable;
- el índice y las URLs lo usan directamente;
- evita repetir la composición y el parseo en cada consulta.

Alternativas descartadas:

- Clave primaria compuesta `(fuente_id, titn)`: obliga a cambiar todas las relaciones y el worker; el resto del sistema ya usa `Edicion.id` entero.
- Propiedad calculada sin columna: simplifica el modelo pero obliga a resolver la fuente en cada documento del índice y en cada elemento de lista.

Para bibliotecas y sucursales se mantiene el `id` entero y se añade `fuente_id` con `UNIQUE (fuente_id, codigo)`. Los códigos visibles siguen siendo los originales; la fuente se añade solo en los códigos de ubicación del índice y la API (`b:<fuente>:<codigo>`, `s:<fuente>:<codigo>`).

### D3. Ejemplares: unicidad de `external_key` acotada por fuente

`Ejemplar` gana `fuente_id` y la unicidad pasa de `external_key` a `(fuente_id, external_key)`. El algoritmo del hash se mantiene intacto para no romper el emparejamiento de los ejemplares de Madrid ya existentes; la fuente se aplica en la consulta de `upsert` y en la restricción.

Alternativa descartada: añadir la fuente al texto del hash. Obligaría a recalcular todos los `external_key` y, como el hash original incluye el código de barras (que no se persiste), no se puede reconstruir con SQL de forma fiable. Acotar la unicidad por fuente resuelve la colisión sin migrar claves.

### D4. Trabajos y scheduler por fuente

`HarvestJob` gana `fuente_id` nullable. `NULL` se reserva para un indexado global; `discover`, `enrich`, `tmdb`, `branches` y el indexado incremental siempre llevan fuente.

- `create_job` y los `enqueue_*` reciben la fuente.
- La deduplicación y las parejas de exclusión se evalúan por fuente. Dos `enrich` de fuentes distintas pueden convivir; un indexado global bloquea todas las fuentes.
- El scheduler recorre las fuentes habilitadas y evalúa intervalos, último trabajo y pendientes por fuente.
- `mark_absent_since`, `select_pending_titns`, `count_pending_titns` y `record_enrich_failure` reciben la fuente para no mezclar catálogos.
- `processed_titns` y el indexado incremental se interpretan dentro de la fuente del trabajo.

### D5. Índice: una sola colección con `fuente` filtrable

Se mantiene un único índice de Meilisearch. Cada documento usa `id = record_id` y añade `fuente` y `fuente_nombre`. `ubicaciones` pasa a `b:<fuente>:<codigo>` y `s:<fuente>:<codigo>`. `fuente` se añade a facetas y atributos filtrables.

Para no romper enlaces y filtros antiguos, `build_filters` normaliza un código de ubicación sin fuente (`b:RBMALC`, `s:BMALC1`) a `b:madrid:...` o `s:madrid:...` antes de consultar.

Alternativa descartada: un índice por fuente. Multiplica la operación, impide una búsqueda única y complica la paginación y las facetas agregadas.

### D6. API: compatibilidad explícita

- `GET /api/records/{record_id}` acepta `<fuente>:<titn>` y, si no hay prefijo, resuelve `madrid:<titn>`. Una fuente desconocida devuelve 404; un identificador mal formado, 422.
- La ficha añade `record_id`, `fuente` y `fuente_nombre`; `source_url` se construye con el perfil de la fuente.
- `GET /api/search` acepta `fuente` y lo combina con el resto de filtros.
- `GET /api/locations` devuelve códigos con fuente y el campo `fuente`.
- Las rutas de listas usan `{record_id}`; un `titn` suelto se resuelve como Madrid.
- `GET /api/libraries` y `/api/stats` pueden seguir agregados; la fuente se añade donde el cliente la necesita para desambiguar.

Alternativa descartada: rutas nuevas del tipo `/api/sources/{fuente}/records/{titn}`. Duplica endpoints, rompe clientes y no aporta nada frente al identificador compuesto.

### D7. Portal: un segmento dinámico y compatibilidad

La carpeta `app/registro/[titn]` pasa a `app/registro/[recordId]`. El segmento acepta `madrid:2101557` y `2101557`; el segundo se resuelve en la API como Madrid. Los enlaces nuevos usan `record.record_id`; los antiguos siguen funcionando sin redirección adicional.

La ficha muestra la etiqueta de la fuente. Con una sola fuente activa no se muestra selector de comunidad; el selector es parte de `ingesta-andalucia`.

Riesgo de URL: los dos puntos son válidos en un segmento de path, pero se codifican como `%3A` en algunos contextos. El portal usará `encodeURIComponent` al construir enlaces y se añadirá una prueba de navegación con `madrid:2101557`.

### D8. Directorio de bibliotecas por fuente

`DirectoryClient` y `refresh_sucursales` reciben la fuente. El emparejamiento de `SUBC` se hace contra `(fuente_id, codigo)` y nunca contra otra fuente. En este cambio solo Madrid declara directorio; una fuente sin directorio no ejecuta la actualización y no falla el resto.

### D9. Configuración y precedencia

`MEDIATECA_OPAC_BASE_URL`, `MEDIATECA_OPAC_PATH` y `MEDIATECA_CRAWL_DELAY` siguen existiendo como valores iniciales y de respaldo. La fila de `fuentes` es la fuente de verdad una vez sembrada. FlareSolverr sigue siendo global en este cambio; la política de captcha se guarda por fuente para poder pausar una sin afectar a las demás.

### D10. Migración y reindexado

La migración `migrate_fuentes.sql` será idempotente y hará, en orden:

1. Crear `fuentes` y sembrar `madrid`.
2. Añadir `fuente_id` a `ediciones`, `bibliotecas`, `sucursales`, `ejemplares` y `harvest_jobs`.
3. Rellenar `fuente_id` con Madrid y `record_id` con `madrid:<titn>`.
4. Añadir `record_id` a `lista_items` y migrar su clave primaria de `(lista_id, titn)` a `(lista_id, record_id)`.
5. Sustituir las unicidades globales por las compuestas y añadir la unicidad `(fuente_id, external_key)` en ejemplares.
6. Actualizar `SCHEMA_VERSION` a `7` mediante el comando de migración.

El `init` actual ejecuta `index` sin reset. Para este despliegue se añadirá una comprobación de versión: si la base pasa de `< 7` a `7`, `init` ejecutará `index --reset`; en arranques posteriores mantendrá el indexado normal. Así el índice no queda con documentos antiguos cuyo `id` es un `TITN` suelto.

Rollback: la migración es incompatible con la imagen anterior de la API. Un rollback de imagen sola no es suficiente; requiere restaurar la copia de seguridad de PostgreSQL y la imagen anterior, o aplicar una migración inversa. El diseño asume copia previa y ventana de mantenimiento.

## Risks / Trade-offs

- **Colisión de `TITN` en logs y URLs** → `record_id` y `fuente` acompañan siempre al `TITN`; los logs antiguos siguen siendo legibles porque el `TITN` se conserva.
- **Reindexado con búsqueda degradada** → ejecutar `index --reset` en la ventana de despliegue; si el volumen crece, valorar un índice temporal con intercambio, fuera de este cambio.
- **`record_id` con `:` en Next.js y proxies** → probar navegación y enlaces compartidos; usar `encodeURIComponent`; la API acepta el valor codificado.
- **Doble enriquecimiento de la misma película en dos fuentes** → aceptado en este cambio; la unificación por TMDB/EAN es el cambio posterior.
- **`Obra` global con agrupación heurística** → no se muestra como resultado único todavía; una fusión errónea se puede auditar y corregir cuando llegue la unificación.
- **Indexado global bloquea todas las fuentes** → el bloqueo dura lo que tarde el reindexado; se documenta como operación de mantenimiento.
- **Directorio solo de Madrid** → las fuentes futuras sin directorio no tendrán cercanía hasta un cambio específico; el modelo ya permite añadirlo por fuente.
- **Compatibilidad de listas** → la migración conserva título y número de elementos; se prueba con una lista histórica y con un `TITN` suelto.

## Migration Plan

1. Copia de seguridad de PostgreSQL y del índice de Meilisearch; anotar `SCHEMA_VERSION` actual.
2. Desplegar la imagen `mediateca-batch` nueva y ejecutar `init`. La migración crea `fuentes`, rellena Madrid, migra listas y deja `SCHEMA_VERSION=7`; al detectar el salto de versión, `init` reconstruye el índice con `--reset`.
3. Desplegar `mediateca-web` nueva.
4. Verificar: búsqueda, `/api/records/2101557`, `/api/records/madrid:2101557`, `/api/locations`, una lista histórica y el enlace `/registro/2101557`.
5. Si falla la verificación, restaurar la base y las imágenes anteriores; no intentar un rollback solo de API sobre el esquema nuevo.

## Open Questions

- Ninguna que bloquee la implementación. La conveniencia de un índice temporal con intercambio sin caída se decidirá cuando el volumen o el tiempo de reindexado lo justifiquen.
