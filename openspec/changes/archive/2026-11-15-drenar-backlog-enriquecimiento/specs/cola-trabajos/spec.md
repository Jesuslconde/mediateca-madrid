# Spec Delta

## MODIFIED Requirements

### Requirement: Programación periódica

El scheduler MUST encolar los trabajos programados sin ejecutar el OPAC y SHALL leer la configuración desde `app_config` en cada comprobación.

#### Scenario: Descubrimiento programado

- **WHEN** se cumple el intervalo de descubrimiento
- **THEN** el scheduler encola un `discover` incremental
- **AND** no encola otro si ya hay uno activo

#### Scenario: Barrido completo programado

- **WHEN** se cumple el intervalo de barrido completo
- **THEN** el scheduler encola un `discover` completo
- **AND** el modo queda registrado en las estadísticas del trabajo

#### Scenario: Enriquecimiento programado

- **WHEN** existen ediciones pendientes de ficha OPAC y se cumple el intervalo de enriquecimiento
- **THEN** el scheduler encola un `enrich` sobre todos los pendientes, sin limitarse a la última cohorte descubierta
- **AND** no encola otro si ya hay un descubrimiento o enriquecimiento activo

## ADDED Requirements

### Requirement: Drenado del backlog de enriquecimiento

Al completar un lote `enrich` con progreso y pendientes restantes, el worker MUST encolar el siguiente lote sobre todos los pendientes y SHALL detenerse cuando no haya progreso, no queden pendientes o se alcance el tope configurado.

#### Scenario: Lote con progreso y pendientes

- **WHEN** un lote `enrich` termina habiendo procesado al menos una ficha y quedan pendientes
- **THEN** se encola un nuevo `enrich` sobre todos los pendientes
- **AND** el nuevo trabajo no duplica uno ya activo

#### Scenario: Backlog histórico drenado

- **WHEN** existen pendientes de descubrimientos anteriores a la última cohorte
- **THEN** los lotes encadenados los incluyen
- **AND** el drenado continúa hasta que no queden pendientes

#### Scenario: Lote sin progreso

- **WHEN** un lote `enrich` termina sin procesar ninguna ficha
- **THEN** no se encola otro lote automáticamente
- **AND** el motivo queda registrado en las estadísticas

#### Scenario: Tope de encadenamientos

- **WHEN** se alcanza el número máximo de lotes encadenados configurado
- **THEN** el drenado se detiene
- **AND** el siguiente intervalo del scheduler puede reanudarlo

#### Scenario: Drenado desactivado

- **WHEN** el drenado está desactivado por configuración
- **THEN** cada job `enrich` procesa un solo lote
- **AND** el scheduler sigue encolando sobre todos los pendientes en el siguiente intervalo

#### Scenario: Trazabilidad

- **WHEN** termina un lote encadenado
- **THEN** las estadísticas incluyen los pendientes restantes, la profundidad del encadenamiento y el motivo de parada
