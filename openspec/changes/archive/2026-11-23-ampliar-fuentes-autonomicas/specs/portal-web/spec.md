# Spec Delta

## ADDED Requirements

### Requirement: Presentación de fuentes de cobertura

El portal SHALL mostrar los resultados y las fichas de fuentes de cobertura con título, año, soportes, géneros y enlace al catálogo oficial, aunque no tengan bibliotecas tenedoras. En ausencia de un filtro de biblioteca SHALL NOT ocultar esos registros ni ofrecer un filtro de disponibilidad.

#### Scenario: Resultado sin bibliotecas

- **WHEN** un resultado pertenece a una fuente de cobertura sin ejemplares
- **THEN** se muestra con su título, año y soportes
- **AND** se ofrece el enlace a su catálogo oficial
- **AND** no se muestra una lista de bibliotecas tenedoras

#### Scenario: Ficha sin bibliotecas

- **WHEN** el usuario abre la ficha de una edición de cobertura
- **THEN** ve sus metadatos y el enlace al catálogo oficial
- **AND** ve un estado vacío de bibliotecas en lugar de un error

#### Scenario: Enlace al catálogo de la fuente

- **WHEN** el usuario pulsa el enlace de la ficha de una edición de cobertura
- **THEN** se abre la URL permanente del catálogo de esa fuente
- **AND** no se usa la URL de Madrid ni una URL global

#### Scenario: Filtro de biblioteca

- **WHEN** el usuario aplica un filtro de biblioteca o sucursal
- **THEN** las ediciones de cobertura sin esa biblioteca no aparecen en el resultado filtrado
- **AND** siguen apareciendo cuando no hay filtro de biblioteca
