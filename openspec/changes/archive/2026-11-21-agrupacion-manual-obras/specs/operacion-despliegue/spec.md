# Spec Delta

## ADDED Requirements

### Requirement: Despliegue de la agrupación manual

La migración de agrupación manual MUST aplicarse desde `services/enrich` y SHALL dejar `SCHEMA_VERSION` en `8`. El despliegue SHALL reconstruir el índice para que los documentos incluyan la referencia de obra.

#### Scenario: Migración sobre una instalación existente
- **WHEN** el operador ejecuta `init` sobre una base con datos
- **THEN** se añaden las columnas de agrupación manual de forma idempotente
- **AND** `SCHEMA_VERSION` queda en `8`
- **AND** las ediciones y obras existentes conservan sus datos

#### Scenario: Reindexado completo
- **WHEN** `init` detecta el salto de versión de esquema
- **THEN** reconstruye el índice con `--reset`
- **AND** cada documento indexado incluye su referencia de obra
- **AND** la búsqueda agrupada queda operativa

#### Scenario: Orden de despliegue
- **WHEN** se despliega el cambio
- **THEN** se reconstruyen `mediateca-batch` y `mediateca-web` desde el mismo commit
- **AND** el servicio `init` aplica la migración y el reindexado antes de arrancar la API
- **AND** la API no ejecuta migraciones ni escribe en el catálogo
