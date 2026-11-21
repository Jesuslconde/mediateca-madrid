# Spec Delta

## ADDED Requirements

### Requirement: Una tarjeta por obra

La página de resultados MUST mostrar una única tarjeta por obra. La tarjeta SHALL indicar el número de ediciones, la unión de soportes y los datos agregados de ejemplares y bibliotecas. La cabecera SHALL distinguir el número de obras del número de ediciones.

#### Scenario: Película con varias ediciones
- **WHEN** el usuario busca una película con cuatro ediciones en la misma obra
- **THEN** ve una sola tarjeta
- **AND** la tarjeta indica que hay cuatro ediciones
- **AND** muestra todos los soportes disponibles entre esas ediciones

#### Scenario: Cabecera con totales
- **WHEN** el usuario consulta resultados agrupados
- **THEN** la cabecera muestra el número de obras y el número de ediciones
- **AND** la paginación corresponde al número de obras

#### Scenario: Edición sin obra
- **WHEN** una edición no pertenece a ninguna obra
- **THEN** aparece en su propia tarjeta
- **AND** la tarjeta indica una sola edición

### Requirement: Ediciones de la misma obra en la ficha

La ficha de registro SHALL mostrar una sección con todas las ediciones de la misma obra, indicando título, año, soportes y número de ejemplares, y SHALL enlazar cada edición a su propia ficha.

#### Scenario: Ficha con varias ediciones
- **WHEN** el usuario abre una edición que tiene ediciones hermanas
- **THEN** la ficha muestra la lista de ediciones de la obra
- **AND** cada entrada enlaza a su `/registro/{record_id}`
- **AND** se distingue la edición que está abierta

#### Scenario: Ficha con una sola edición
- **WHEN** la edición es la única de su obra
- **THEN** la ficha no muestra la sección de ediciones hermanas
- **AND** el resto de la ficha no cambia
