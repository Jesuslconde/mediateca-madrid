# Spec Delta

## ADDED Requirements

### Requirement: Registro de sucursales

Cada sucursal MUST almacenarse con un código único, su biblioteca, nombre, municipio, dirección, código postal y coordenadas opcionales. Los campos de ubicación SHALL admitir valor vacío cuando el directorio no los aporte.

#### Scenario: Sucursal con ubicación completa

- **WHEN** se guarda una sucursal con código, biblioteca, nombre, municipio, dirección, código postal, latitud y longitud
- **THEN** se conservan todos los campos
- **AND** el código de sucursal queda registrado una sola vez

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** se guarda una sucursal con código postal pero sin latitud ni longitud
- **THEN** se conserva el código postal
- **AND** la latitud y la longitud quedan vacías

#### Scenario: Sucursal sin ubicación

- **WHEN** se guarda una sucursal sin municipio, dirección, código postal ni coordenadas
- **THEN** la sucursal existe con su código y nombre
- **AND** no se inventan datos de ubicación

#### Scenario: Código duplicado

- **WHEN** se vuelve a guardar una sucursal con un código ya existente
- **THEN** se actualiza la sucursal existente
- **AND** no se crea un duplicado

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

## MODIFIED Requirements

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
