# Spec Delta

## ADDED Requirements

### Requirement: Agrupación manual persistente de ediciones

Cada edición SHALL poder marcarse como agrupada manualmente mediante `obra_manual`, con fecha `obra_manual_at`. La marca SHALL prevalecer sobre la asignación automática y SHALL conservarse mientras el operador no la revierta.

#### Scenario: Edición agrupada manualmente
- **WHEN** el operador asigna una edición a una obra desde el dashboard
- **THEN** la edición queda con `obra_manual = true` y `obra_manual_at`
- **AND** la obra destino queda marcada como manual

#### Scenario: Reingesta de una edición manual
- **WHEN** se vuelve a enriquecer una edición con `obra_manual = true`
- **THEN** la edición conserva su `obra_id`
- **AND** no se aplica la heurística automática de agrupación

#### Scenario: Edición nueva en obra manual
- **WHEN** una edición nueva coincide en título uniforme y año con una obra manual
- **THEN** la edición se añade a esa obra
- **AND** queda marcada como manual

### Requirement: Obra manual única por título y año

Una obra manual MUST respetar la unicidad de `(titulo_uniforme, anio)`. Si ya existe una obra con esa clave, el sistema SHALL reutilizarla y SHALL NOT crear una segunda obra.

#### Scenario: Obra destino existente
- **WHEN** el operador crea una agrupación con un título uniforme y año que ya existen
- **THEN** se reutiliza la obra existente
- **AND** no se crea una obra duplicada

#### Scenario: Obra manual nueva
- **WHEN** el operador crea una agrupación con una clave que no existe
- **THEN** se crea una obra con `manual = true`
- **AND** las ediciones seleccionadas quedan asociadas a ella

### Requirement: Desvinculación de la agrupación manual

Una edición SHALL poder volver al comportamiento automático. Al desvincularla, el sistema SHALL limpiar `obra_manual` y recalcular su obra con la heurística vigente.

#### Scenario: Volver a automático
- **WHEN** el operador desvincula una edición agrupada manualmente
- **THEN** `obra_manual` queda en `false`
- **AND** la edición se reasigna según título uniforme y año
- **AND** la obra anterior deja de ser manual si no conserva ediciones manuales
