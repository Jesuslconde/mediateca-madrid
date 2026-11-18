# Spec Delta

## MODIFIED Requirements

### Requirement: Cobertura del catálogo

El sistema SHALL mostrar el número de ediciones descubiertas, enriquecidas, pendientes y fallidas, junto con el porcentaje de enriquecimiento sobre el total y el desglose por fuente.

#### Scenario: Cobertura parcial

- **WHEN** se han enriquecido parte de las ediciones del catálogo
- **THEN** la vista muestra los conteos y el porcentaje de enriquecimiento
- **AND** el número de pendientes coincide con las ediciones sin enriquecer
- **AND** cada fuente habilitada muestra su propio desglose

#### Scenario: Catálogo vacío

- **WHEN** no existen ediciones
- **THEN** la vista muestra cero en todas las métricas
- **AND** el porcentaje de enriquecimiento se muestra como cero sin dividir por cero

## ADDED Requirements

### Requirement: Fuente en la operación del dashboard

El dashboard MUST identificar la fuente en la cobertura, en la tabla de catálogo y en los trabajos recientes. Las acciones de encolado SHALL indicar la fuente sobre la que operan y SHALL rechazar un duplicado solo cuando coincidan tipo y fuente. Las fuentes deshabilitadas SHALL mostrarse como tales y SHALL NOT ofrecer acciones de ingesta.

#### Scenario: Cobertura por fuente

- **WHEN** el operador abre la página de Inicio con varias fuentes
- **THEN** ve el total del catálogo y el desglose de cada fuente
- **AND** las fuentes deshabilitadas aparecen identificadas

#### Scenario: Encolar una tarea con fuente

- **WHEN** el operador pulsa una acción de descubrimiento o enriquecimiento
- **THEN** el trabajo se crea para la fuente seleccionada
- **AND** el mensaje de confirmación identifica esa fuente

#### Scenario: Catálogo con fuente

- **WHEN** el operador consulta la tabla de catálogo
- **THEN** cada fila muestra la fuente de la edición
- **AND** puede filtrar por fuente

#### Scenario: Fuente deshabilitada

- **WHEN** una fuente está deshabilitada
- **THEN** sus acciones de ingesta no están disponibles
- **AND** sus datos siguen visibles en la cobertura y en el catálogo
