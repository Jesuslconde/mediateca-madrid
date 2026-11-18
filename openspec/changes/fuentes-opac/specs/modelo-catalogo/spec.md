# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
