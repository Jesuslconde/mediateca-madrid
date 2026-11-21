# Spec Delta

## ADDED Requirements

### Requirement: Precedencia de la agrupación manual en la ingesta

El enriquecimiento y la reingesta MUST NOT reasignar el `obra_id` de una edición con `obra_manual = true`. Las ediciones sin esa marca SHALL seguir usando la heurística automática de título uniforme y año.

#### Scenario: Reingesta de una edición manual
- **WHEN** se vuelve a procesar una edición agrupada manualmente
- **THEN** la edición conserva su `obra_id` y su marca `obra_manual`
- **AND** no se crea ni se reutiliza otra obra para esa edición

#### Scenario: Edición automática
- **WHEN** se procesa una edición sin agrupación manual
- **THEN** la asignación de obra sigue la heurística de título uniforme y año
- **AND** la edición no queda marcada como manual

#### Scenario: Edición nueva en una obra manual
- **WHEN** se procesa una edición nueva cuya clave coincide con una obra manual
- **THEN** la edición se asocia a esa obra
- **AND** queda marcada como manual
