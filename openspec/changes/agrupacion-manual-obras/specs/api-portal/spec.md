# Spec Delta

## ADDED Requirements

### Requirement: Búsqueda agrupada por obra

`GET /api/search` MUST devolver como máximo un resultado por obra. Cada resultado SHALL indicar `obra_id`, `obra_titulo`, el número de ediciones y los datos agregados de soportes, bibliotecas y ejemplares. La respuesta SHALL incluir el total de obras y el total de ediciones.

#### Scenario: Resultado con varias ediciones
- **WHEN** el cliente busca un título que tiene varias ediciones en una obra
- **THEN** recibe un único resultado para la obra
- **AND** el resultado incluye `obra_id`, `obra_titulo` y `ediciones_count`
- **AND** `soportes`, `bibliotecas` y `ejemplares` agregan todas las ediciones de la obra

#### Scenario: Resultado sin obra
- **WHEN** una edición no tiene obra
- **THEN** aparece como un resultado propio
- **AND** `ediciones_count` vale `1`

#### Scenario: Totales de la búsqueda
- **WHEN** el cliente consulta `/api/search`
- **THEN** la respuesta incluye `total` con el número de obras
- **AND** incluye `total_ediciones` con el número de ediciones
- **AND** las facetas siguen contando ediciones

### Requirement: Ediciones de la obra en la ficha

`GET /api/records/{record_id}` SHALL incluir, cuando la edición tenga obra, la lista de ediciones de esa obra con `record_id`, `fuente`, `titn`, título, año, soportes, `ean`, número de ejemplares y `source_url`.

#### Scenario: Ficha con ediciones hermanas
- **WHEN** el cliente solicita una edición que pertenece a una obra con varias ediciones
- **THEN** la respuesta incluye la lista de ediciones de la obra
- **AND** cada edición conserva su `record_id`, su fuente y su URL del OPAC

#### Scenario: Ficha sin ediciones hermanas
- **WHEN** la edición no tiene obra o es la única edición de su obra
- **THEN** la lista de ediciones contiene como máximo la edición actual
- **AND** la ficha sigue siendo válida

#### Scenario: Compatibilidad de la ficha
- **WHEN** un cliente anterior consume una ficha
- **THEN** sigue recibiendo los campos existentes
- **AND** los nuevos campos de ediciones son opcionales
