# Spec Delta

## MODIFIED Requirements

### Requirement: Inicialización de base de datos

La imagen `mediateca-batch` MUST ofrecer comandos idempotentes para crear el esquema y el índice. La API SHALL NOT crear ni migrar el esquema y SHALL validar que la versión compartida es compatible al arrancar. El servicio `init` MUST ejecutarse antes que la API y el portal y SHALL aplicar la migración de fuentes antes de que la API arranque.

#### Scenario: Primer arranque

- **WHEN** se ejecuta el servicio `init`
- **THEN** se crean las tablas y el índice de Meilisearch si no existen
- **AND** se aplican las migraciones idempotentes
- **AND** puede ejecutarse de nuevo sin errores

#### Scenario: Migración de identidad global

- **WHEN** se ejecuta `init` sobre una base con el esquema anterior
- **THEN** se crea el registro de fuentes y se siembra `madrid`
- **AND** se rellenan las referencias de fuente de las entidades existentes
- **AND** `SCHEMA_VERSION` queda en `7`

#### Scenario: API sobre un esquema existente

- **WHEN** la API arranca contra una base ya inicializada
- **THEN** no ejecuta migraciones ni escrituras de esquema
- **AND** falla con un error legible si el esquema o la versión no son compatibles

### Requirement: Almacenamiento compartido y orden de despliegue

PostgreSQL y Meilisearch SHALL ser compartidos por todos los servicios. La ingesta MUST ser el único dueño de las migraciones y de las escrituras del catálogo y del índice. La API SHALL leer el catálogo y el índice y SHALL escribir únicamente las tablas de listas; SHALL NOT modificar tablas del catálogo ni del índice. Los modelos MUST proceder de `packages/shared` y las dos imágenes SHALL construirse en el mismo commit. El despliegue de la identidad global SHALL incluir la migración y la reconstrucción del índice.

#### Scenario: Migración antes de desplegar la API

- **WHEN** cambia el esquema o el contrato compartido
- **THEN** se actualizan los modelos y la migración en el mismo commit
- **AND** se reconstruyen `mediateca-batch` y `mediateca-web`
- **AND** el servicio `init` aplica las migraciones antes de arrancar la API

#### Scenario: Fallo de la API tras una migración

- **WHEN** la API no arranca con el esquema migrado
- **THEN** se puede revertir la API a la imagen anterior sin deshacer los datos
- **AND** la ingesta sigue siendo la única fuente de escritura del catálogo y del índice

#### Scenario: Despliegue con índice reconstruido

- **WHEN** se despliega este cambio sobre una instalación existente
- **THEN** el operador ejecuta la migración y el reindexado completo
- **AND** el índice anterior no deja documentos con identificadores sin fuente
- **AND** las URLs antiguas de Madrid siguen resolviendo a la edición correcta

## ADDED Requirements

### Requirement: Reindexado por cambio de identidad

La identidad global `record_id` SHALL requerir un reindexado completo explícito. El sistema SHALL NOT reutilizar documentos del índice anterior que usen `TITN` como clave.

#### Scenario: Reindexado completo

- **WHEN** el operador ejecuta `mediateca index --reset` tras la migración
- **THEN** el índice se vacía y se reconstruye con `record_id` como clave
- **AND** cada documento incluye su fuente
- **AND** la búsqueda no devuelve documentos duplicados ni huérfanos

#### Scenario: Reindexado omitido

- **WHEN** la migración se aplica pero el índice no se reconstruye
- **THEN** el sistema no debe considerarse listo para producción
- **AND** la documentación de despliegue indica el paso pendiente
