# Spec Delta

## MODIFIED Requirements

### Requirement: Compatibilidad y evolucion

Los cambios incompatibles del modelo compartido MUST incrementar `SCHEMA_VERSION` y SHALL requerir un despliegue coordinado. La API SHALL validar al arrancar que el esquema de la base de datos coincide con `SCHEMA_VERSION`. La agrupación manual de obras SHALL subir `SCHEMA_VERSION` a `8`.

#### Scenario: Cambio incompatible
- **WHEN** se elimina o renombra un campo del modelo compartido
- **THEN** `SCHEMA_VERSION` aumenta
- **AND** `init` aplica la migracion antes de arrancar la API
- **AND** las dos imagenes se reconstruyen desde el mismo commit

#### Scenario: Migracion de identidad
- **WHEN** se aplica la migracion de fuentes sobre una base existente
- **THEN** `SCHEMA_VERSION` queda en `8`
- **AND** las ediciones, bibliotecas, sucursales, ejemplares y listas existentes quedan asociados a `madrid`
- **AND** la migracion puede ejecutarse de nuevo sin duplicar datos

#### Scenario: Migracion de agrupacion manual
- **WHEN** se aplica la migracion de agrupacion manual sobre una base existente
- **THEN** existen las columnas `ediciones.obra_manual`, `ediciones.obra_manual_at`, `obras.manual` y `obras.updated_at`
- **AND** `schema_meta.schema_version` queda en `8`
- **AND** la migracion puede ejecutarse de nuevo sin errores

#### Scenario: Version incompatible en arranque
- **WHEN** un servicio arranca con un esquema incompatible
- **THEN** falla el arranque con un error legible
- **AND** no escribe datos con un esquema desconocido

## ADDED Requirements

### Requirement: Campos de agrupación en el contrato

El contrato OpenAPI SHALL describir los campos de agrupación de los resultados y de la ficha. Los nuevos campos SHALL ser opcionales o tener valor por defecto para no romper a los clientes existentes.

#### Scenario: Resultado de búsqueda agrupado
- **WHEN** el contrato describe un resultado de búsqueda
- **THEN** incluye `obra_id`, `obra_titulo` y `ediciones_count`
- **AND** la respuesta de búsqueda incluye `total_ediciones`

#### Scenario: Ficha con ediciones de la obra
- **WHEN** el contrato describe la obra de una ficha
- **THEN** incluye la lista de ediciones de la obra con su `record_id`, `fuente`, `titn`, título, año, soportes, `ean`, ejemplares y `source_url`

#### Scenario: Compatibilidad con clientes antiguos
- **WHEN** un cliente generado con el contrato anterior consume la nueva API
- **THEN** sigue compilando
- **AND** los campos nuevos son opcionales o tienen valor por defecto
