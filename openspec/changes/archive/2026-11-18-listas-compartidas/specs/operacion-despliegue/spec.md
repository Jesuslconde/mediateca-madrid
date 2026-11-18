# Spec Delta

## MODIFIED Requirements

### Requirement: Almacenamiento compartido y orden de despliegue

PostgreSQL y Meilisearch SHALL ser compartidos por todos los servicios. La ingesta MUST ser el único dueño de las migraciones y de las escrituras del catálogo y del índice. La API SHALL leer el catálogo y el índice y SHALL escribir únicamente las tablas de listas; SHALL NOT modificar tablas del catálogo ni del índice. Los modelos MUST proceder de `packages/shared` y las dos imágenes SHALL construirse en el mismo commit.

#### Scenario: Migración antes de desplegar la API

- **WHEN** cambia el esquema o el contrato compartido
- **THEN** se actualizan los modelos y la migración en el mismo commit
- **AND** se reconstruyen `mediateca-batch` y `mediateca-web`
- **AND** el servicio `init` aplica las migraciones antes de arrancar la API

#### Scenario: Fallo de la API tras una migración

- **WHEN** la API no arranca con el esquema migrado
- **THEN** se puede revertir la API a la imagen anterior sin deshacer los datos
- **AND** la ingesta sigue siendo la única fuente de escritura del catálogo y del índice

## ADDED Requirements

### Requirement: Mantenimiento de listas en la inicialización

El servicio `init` SHALL eliminar las listas caducadas después de aplicar las migraciones y antes de arrancar la API. La limpieza MUST ser idempotente y SHALL NOT afectar a las listas vigentes.

#### Scenario: Limpieza en el arranque

- **WHEN** se ejecuta el servicio `init`
- **THEN** se eliminan las listas con `expires_at` vencido y sus elementos
- **AND** las listas vigentes permanecen intactas
- **AND** el servicio puede ejecutarse de nuevo sin errores
