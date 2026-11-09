# Spec Delta

## ADDED Requirements

### Requirement: Ingesta separada de la API

La recolección MUST ejecutarse únicamente en el proyecto de ingesta `mediateca-madrid-enrich`. La API y el portal SHALL NOT iniciar recolecciones, escribir metadatos ni modificar el índice, y SHALL leer los datos publicados en el almacenamiento compartido.

#### Scenario: Arranque de la API sin ingesta

- **WHEN** la API arranca
- **THEN** no inicia sesión contra el OPAC ni ejecuta recolecciones
- **AND** comprueba la conexión con PostgreSQL y Meilisearch en modo lectura

#### Scenario: Recolección en el proyecto de ingesta

- **WHEN** se ejecuta una recolección, un descubrimiento o un enriquecimiento
- **THEN** se ejecuta en `mediateca-madrid-enrich`
- **AND** los resultados quedan disponibles para la API en la base de datos compartida

### Requirement: Escritura única del catálogo

Solo el proyecto de ingesta SHALL escribir en las tablas del catálogo y en el índice de búsqueda. Cualquier otro proceso SHALL tratar esos almacenamientos como solo lectura.

#### Scenario: Intento de escritura desde la API

- **WHEN** un proceso de la API intenta crear o actualizar una edición
- **THEN** la operación no forma parte del flujo soportado
- **AND** la API solo expone lecturas del catálogo

#### Scenario: Índice actualizado por la ingesta

- **WHEN** la ingesta termina de enriquecer un lote
- **THEN** actualiza el índice compartido
- **AND** la API sirve los cambios sin reconstruir el índice por su cuenta
