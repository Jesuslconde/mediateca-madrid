# Spec Delta

## ADDED Requirements

### Requirement: Referencia de obra en el documento de índice

El documento de cada edición MUST incluir `obra_id`, `obra_key` y `obra_titulo`. `obra_key` SHALL ser `obra:<id>` cuando la edición tenga obra y `edicion:<record_id>` cuando no la tenga. Los campos SHALL ser filtrables en Meilisearch.

#### Scenario: Edición con obra
- **WHEN** se indexa una edición asociada a una obra
- **THEN** el documento incluye su `obra_id`, un `obra_key` con el identificador de la obra y su `obra_titulo`
- **AND** `obra_key` es único por obra

#### Scenario: Edición sin obra
- **WHEN** se indexa una edición sin obra
- **THEN** el documento incluye `obra_id` vacío
- **AND** `obra_key` usa el `record_id` de la edición
- **AND** no se agrupa con otras ediciones sin obra

#### Scenario: Reindexado tras agrupar
- **WHEN** una edición cambia de obra manualmente
- **THEN** su documento se actualiza con el nuevo `obra_id` y `obra_key`
- **AND** las demás ediciones de la obra anterior no cambian de documento

### Requirement: Resultados agrupados por obra

La búsqueda MUST devolver como máximo un resultado por `obra_key`. Las ediciones de una misma obra SHALL representarse mediante una edición representativa y las ediciones sin obra SHALL seguir apareciendo individualmente.

#### Scenario: Varias ediciones de una obra
- **WHEN** el usuario busca un título con varias ediciones en la misma obra
- **THEN** la respuesta contiene un único resultado para esa obra
- **AND** el resultado identifica la edición representativa

#### Scenario: Ediciones sin obra
- **WHEN** varias ediciones no tienen obra
- **THEN** cada una aparece como un resultado independiente
- **AND** no se agrupan entre sí

#### Scenario: Paginación agrupada
- **WHEN** el usuario navega por páginas de resultados agrupados
- **THEN** la paginación cuenta obras, no ediciones
- **AND** no se repite una obra en varias páginas

### Requirement: Totales y facetas con agrupación

La respuesta de búsqueda MUST distinguir el total de obras del total de ediciones. Las facetas SHALL seguir contando ediciones y SHALL NOT incluir disponibilidad de préstamo.

#### Scenario: Totales diferenciados
- **WHEN** el usuario busca un término con varias ediciones por obra
- **THEN** la respuesta incluye el número de obras y el número de ediciones
- **AND** el total de obras coincide con los resultados paginables

#### Scenario: Facetas por edición
- **WHEN** el usuario consulta las facetas de una búsqueda agrupada
- **THEN** los contadores de soporte, género, idioma, país y fuente cuentan ediciones
- **AND** la respuesta indica también el total de ediciones
