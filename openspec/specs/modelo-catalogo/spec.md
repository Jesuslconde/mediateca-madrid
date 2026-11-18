# modelo-catalogo Specification

## Purpose
Representar el catálogo en tres niveles (obra, edición y ejemplar) para agrupar las distintas versiones de una película y conservar la disponibilidad física por biblioteca.

## Requirements

### Requirement: Separación obra, edición y ejemplar

El modelo de datos MUST distinguir la obra (película), la edición (registro bibliográfico y soporte) y el ejemplar (copia física en una sucursal). La obra SHALL ser global y podrá agrupar ediciones de distintas fuentes; cada edición SHALL pertenecer a una fuente y conservar su `TITN`; cada ejemplar SHALL conservar la biblioteca y la sucursal de la misma fuente que la edición.

#### Scenario: Película con DVD y Blu-ray

- **WHEN** existen dos registros de la misma película, uno en DVD y otro en Blu-ray
- **THEN** ambos se agrupan bajo la misma obra
- **AND** cada uno conserva su propio `TITN`, soporte y ejemplares

#### Scenario: Misma película en dos fuentes

- **WHEN** dos fuentes describen la misma película con el mismo título uniforme y año
- **THEN** ambas ediciones pueden compartir la misma obra
- **AND** cada edición conserva su fuente, su `TITN` y sus propios ejemplares

#### Scenario: Ejemplares de fuentes distintas

- **WHEN** una obra agrupa ediciones de varias fuentes
- **THEN** los ejemplares de cada edición quedan bajo su fuente
- **AND** no se mezclan bibliotecas ni sucursales de fuentes distintas

### Requirement: Identificación estable

Cada edición MUST identificarse por su `record_id`, compuesto por el código de fuente y el `TITN` (`<fuente>:<titn>`). La pareja `(fuente, titn)` SHALL ser única y el EAN y la combinación de título, año y director SHALL usarse como señales secundarias de agrupación.

#### Scenario: Reproceso de un registro

- **WHEN** se vuelve a procesar un `TITN` ya existente en la misma fuente
- **THEN** se actualiza el registro existente
- **AND** no se crea un duplicado

#### Scenario: Mismo TITN en dos fuentes

- **WHEN** dos fuentes tienen un registro con el mismo `TITN`
- **THEN** existen dos ediciones con `record_id` distintos
- **AND** cada una conserva sus propios metadatos y ejemplares

#### Scenario: Edición histórica de Madrid

- **WHEN** se migra una edición existente sin fuente
- **THEN** queda asociada a `madrid`
- **AND** su `record_id` se calcula como `madrid:<titn>`

### Requirement: Normalización de metadatos

El parser MUST normalizar espacios, puntuación final, años, duración en minutos, idioma, país y roles de autoría antes de persistir. El título MUST ser el título propio completo, sin mención de responsabilidad ni puntuación ISBD final.

#### Scenario: Duración extraída de la descripción física

- **WHEN** la descripción física contiene `1 DVD-Video (ca. 129 min)`
- **THEN** la edición guarda `duracion_min = 129`

#### Scenario: Título con subtítulo

- **WHEN** la ficha muestra `Historia cinematográfica de la Unión Europea : legislación cinematográfica europea /`
- **THEN** la edición guarda `Historia cinematográfica de la Unión Europea : legislación cinematográfica europea`
- **AND** no guarda la mención de responsabilidad

#### Scenario: Título con puntuación final

- **WHEN** el título termina en ` /`, ` :`, ` ;`, ` ,`, `.` o `=`
- **THEN** la puntuación final se elimina
- **AND** se conservan `?`, `!`, corchetes y paréntesis

#### Scenario: Título uniforme con puntuación final

- **WHEN** el título uniforme termina en puntuación ISBD
- **THEN** se elimina la puntuación final
- **AND** se conservan sus calificadores entre paréntesis

### Requirement: Personas y materias

Las personas MUST almacenarse una sola vez y relacionarse con la edición mediante un rol; las materias y géneros SHALL normalizarse para permitir facetas.

#### Scenario: Director y actor en la misma edición

- **WHEN** una edición tiene una persona como directora y otra como actor
- **THEN** ambas relaciones se guardan con roles distintos
- **AND** no se duplica la persona si ya existía

### Requirement: Tenencia por biblioteca

Cada ejemplar MUST registrar biblioteca, sucursal, signatura, tipo de ejemplar y soporte. El sistema SHALL NOT almacenar estado de préstamo ni historial de disponibilidad, y SHALL deducir la lista de bibliotecas tenedoras a partir de los ejemplares.

#### Scenario: Ficha creada con ejemplares

- **WHEN** se crea la ficha de una edición con ejemplares en varias bibliotecas
- **THEN** cada ejemplar conserva su biblioteca, sucursal, signatura, tipo y soporte
- **AND** la edición expone la lista de bibliotecas que poseen el título

#### Scenario: Edición sin ejemplares

- **WHEN** una edición no tiene ejemplares registrados
- **THEN** su lista de bibliotecas tenedoras queda vacía
- **AND** no se inventa ninguna biblioteca

#### Scenario: Sin estado de préstamo

- **WHEN** se guarda o actualiza un ejemplar
- **THEN** no se persiste ningún campo de disponibilidad de préstamo
- **AND** no se añade ninguna entrada de historial de disponibilidad

### Requirement: Modelo compartido y versión única

El modelo de datos MUST definirse en `packages/shared`. La ingesta y la API SHALL usar la misma fuente de modelos en el monorepo, y solo la ingesta SHALL aplicar migraciones o escribir en las tablas del catálogo.

#### Scenario: Misma fuente de modelos

- **WHEN** la ingesta y la API se construyen desde el monorepo
- **THEN** ambas instalan el paquete local `mediateca-shared`
- **AND** no existen copias locales ni wheels versionados de los modelos

#### Scenario: Lectura con modelo compartido

- **WHEN** la API consulta obras, ediciones o ejemplares
- **THEN** usa el modelo compartido en modo lectura
- **AND** no crea ni modifica tablas ni registros

#### Scenario: Migración desde la ingesta

- **WHEN** cambia el esquema del catálogo
- **THEN** la migración se aplica desde `services/enrich`
- **AND** la API solo consume el esquema resultante

### Requirement: Campos de enriquecimiento TMDB en la edición

Cada edición MUST poder almacenar `paises_origen` como lista de códigos ISO 3166-1 alfa-2 en mayúsculas, `tmdb_id` como identificador numérico opcional y `tmdb_enriched_at` como fecha opcional de sincronización. La lista SHALL admitir el valor vacío cuando no haya países conocidos.

#### Scenario: Edición emparejada en TMDB

- **WHEN** una edición se empareja con una película de TMDB
- **THEN** la edición guarda su `tmdb_id`, la lista `paises_origen` y `tmdb_enriched_at`

#### Scenario: Edición sin emparejar

- **WHEN** una edición no se empareja con TMDB
- **THEN** la edición conserva `paises_origen` como lista vacía
- **AND** `tmdb_id` y `tmdb_enriched_at` permanecen vacíos

### Requirement: Independencia del país del OPAC

El campo `pais` procedente del OPAC MUST conservarse como dato independiente de `paises_origen`. La actualización de los campos TMDB SHALL NOT sobrescribir, vaciar ni reinterpretar `pais`.

#### Scenario: Edición con país del OPAC y países de TMDB

- **WHEN** una edición tiene `pais` del OPAC y además se enriquece con TMDB
- **THEN** se conservan ambos datos
- **AND** `pais` mantiene el valor original del MARC

#### Scenario: Edición sin país en el OPAC

- **WHEN** una edición no tiene `pais` del OPAC
- **THEN** `paises_origen` puede contener los países obtenidos de TMDB
- **AND** no se inventa un `pais` del OPAC

### Requirement: Columnas de estado de enriquecimiento

Cada edición MUST almacenar el estado de enriquecimiento OPAC y TMDB con las columnas `enrich_status`, `enrich_attempts`, `enrich_last_attempt_at`, `enrich_last_error`, `tmdb_status`, `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error`. La migración SHALL ser idempotente y `SCHEMA_VERSION` SHALL pasar a `5`.

#### Scenario: Migración idempotente

- **WHEN** se aplica la migración sobre una base con o sin las columnas
- **THEN** las columnas quedan creadas una sola vez
- **AND** `schema_meta.schema_version` queda en `5`

#### Scenario: Valores por defecto

- **WHEN** se crea una edición nueva
- **THEN** `enrich_status` y `tmdb_status` valen `pending`
- **AND** los contadores de intentos valen `0`

#### Scenario: Ediciones existentes

- **WHEN** la migración se aplica sobre ediciones ya enriquecidas
- **THEN** `enrich_status` queda en `enriched`
- **AND** `tmdb_status` queda en `matched` si tienen `tmdb_enriched_at`
- **AND** el resto queda en `pending`

### Requirement: Registro de sucursales

Cada sucursal MUST almacenarse con un código único dentro de su fuente, su biblioteca, nombre, municipio, dirección, código postal y coordenadas opcionales. Los campos de ubicación SHALL admitir valor vacío cuando el directorio no los aporte.

#### Scenario: Sucursal con ubicación completa

- **WHEN** se guarda una sucursal con código, biblioteca, nombre, municipio, dirección, código postal, latitud y longitud
- **THEN** se conservan todos los campos
- **AND** el código de sucursal queda registrado una sola vez dentro de su fuente

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** se guarda una sucursal con código postal pero sin latitud ni longitud
- **THEN** se conserva el código postal
- **AND** la latitud y la longitud quedan vacías

#### Scenario: Sucursal sin ubicación

- **WHEN** se guarda una sucursal sin municipio, dirección, código postal ni coordenadas
- **THEN** la sucursal existe con su código y nombre
- **AND** no se inventan datos de ubicación

#### Scenario: Código duplicado

- **WHEN** se vuelve a guardar una sucursal con un código ya existente en su fuente
- **THEN** se actualiza la sucursal existente
- **AND** no se crea un duplicado

#### Scenario: Mismo código en fuentes distintas

- **WHEN** dos fuentes usan el mismo código de sucursal
- **THEN** existen dos sucursales distintas
- **AND** cada una queda bajo su fuente y su biblioteca

### Requirement: Resolución de sucursal por código

Cada ejemplar SHALL poder resolverse a una sucursal por su `sucursal_codigo`; si no existe coincidencia, la ubicación de la sucursal SHALL considerarse ausente y SHALL NOT inventarse.

#### Scenario: Ejemplar con sucursal conocida

- **WHEN** un ejemplar tiene un `sucursal_codigo` que coincide con una sucursal almacenada
- **THEN** el ejemplar puede resolver la ubicación de esa sucursal

#### Scenario: Ejemplar sin coincidencia

- **WHEN** un ejemplar tiene un `sucursal_codigo` que no coincide con ninguna sucursal
- **THEN** la ubicación de la sucursal se considera ausente
- **AND** la ubicación de la biblioteca queda disponible como respaldo

#### Scenario: Ejemplar sin código de sucursal

- **WHEN** un ejemplar no tiene `sucursal_codigo`
- **THEN** no se le asigna ninguna ubicación de sucursal
- **AND** no se inventa una sucursal

### Requirement: Código postal de biblioteca

Cada biblioteca SHALL poder almacenar un código postal opcional y sus datos de ubicación para servir de respaldo cuando un ejemplar no tenga sucursal.

#### Scenario: Biblioteca con ubicación

- **WHEN** se guarda una biblioteca con municipio, dirección, código postal y coordenadas
- **THEN** esos datos quedan disponibles como ubicación de respaldo

#### Scenario: Biblioteca sin ubicación

- **WHEN** una biblioteca no tiene datos de ubicación
- **THEN** sus campos de ubicación quedan vacíos
- **AND** no se inventan coordenadas ni código postal

### Requirement: Bibliotecas por fuente

Cada biblioteca MUST pertenecer a una fuente y su código SHALL ser único dentro de esa fuente. Los ejemplares SHALL quedar vinculados a una biblioteca de la misma fuente que su edición.

#### Scenario: Mismo código de biblioteca en dos fuentes

- **WHEN** dos fuentes declaran una biblioteca con el mismo código
- **THEN** existen dos bibliotecas distintas
- **AND** cada una conserva su nombre y su fuente

#### Scenario: Coherencia de ejemplar y edición

- **WHEN** se guarda un ejemplar de una edición
- **THEN** su biblioteca pertenece a la misma fuente que la edición
- **AND** no se reutiliza una biblioteca de otra fuente por coincidencia de código
