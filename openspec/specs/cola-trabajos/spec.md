# cola-trabajos Specification

## Purpose

Ejecutar trabajos de ingesta largos y reanudables fuera del scheduler, con una cola persistente en PostgreSQL y un worker que procesa un trabajo cada vez.

## Requirements

### Requirement: Encolado de trabajos

El sistema MUST permitir encolar trabajos de tipo `discover`, `enrich` e `index` con un lote y un cursor inicial desde la CLI, el dashboard o el scheduler.

#### Scenario: Encolar enriquecimiento

- **WHEN** el scheduler encola un trabajo de enriquecimiento de 5.000 fichas
- **THEN** el trabajo queda en estado `pending`
- **AND** el worker puede reclamarlo

#### Scenario: Encolar desde el dashboard

- **WHEN** el operador solicita un trabajo bajo demanda
- **THEN** se crea un trabajo `pending` con el tipo y lote solicitados
- **AND** el dashboard no ejecuta la ingesta

### Requirement: Reclamo atómico

El worker MUST reclamar un trabajo con una operación atómica que impida que dos workers ejecuten el mismo trabajo.

#### Scenario: Dos workers a la vez

- **WHEN** dos workers intentan reclamar el mismo trabajo
- **THEN** solo uno lo obtiene
- **AND** el otro recibe `NULL` o el siguiente trabajo disponible

### Requirement: Ejecución y heartbeat

El worker MUST actualizar un heartbeat mientras ejecuta un trabajo y SHALL marcar como fallido un trabajo cuyo heartbeat haya caducado.

#### Scenario: Worker caído

- **WHEN** un worker deja de actualizar el heartbeat
- **THEN** el trabajo puede ser reclamado de nuevo tras el timeout
- **AND** se registra el intento fallido

### Requirement: Reintentos y backoff

Los trabajos fallidos MUST reintentarse hasta `max_attempts` con backoff exponencial y SHALL terminar en `failed` cuando se agoten.

#### Scenario: Fallo temporal

- **WHEN** un trabajo falla por un error temporal
- **THEN** vuelve a `pending` con un intento más
- **AND** el siguiente intento espera un tiempo mayor

### Requirement: Concurrencia controlada

El sistema SHALL limitar la concurrencia a un trabajo de ingesta a la vez por defecto, configurable mediante variables de entorno.

#### Scenario: Un solo trabajo pesado

- **WHEN** hay un descubrimiento en ejecución
- **THEN** el worker no inicia otro descubrimiento o enriquecimiento
- **AND** los trabajos de indexación pueden esperar a que termine el lote

### Requirement: Deduplicación de trabajos

El sistema MUST impedir que existan dos trabajos activos del mismo tipo y SHALL devolver un error comprensible cuando se intente encolar un duplicado.

#### Scenario: Duplicado activo

- **WHEN** ya hay un `discover`, `enrich` o `index` en estado `pending` o `running`
- **THEN** un nuevo encolado del mismo tipo se rechaza
- **AND** el trabajo existente no se modifica

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

### Requirement: Enriquecimiento encadenado

Al terminar un descubrimiento con nuevos registros, el worker MUST encolar un enriquecimiento para esos registros y SHALL evitar duplicados.

#### Scenario: Descubrimiento con novedades

- **WHEN** un `discover` termina habiendo procesado al menos un registro nuevo
- **THEN** se encola un `enrich` con `since` igual al inicio del descubrimiento
- **AND** el enriquecimiento procesa solo los stubs descubiertos desde ese instante

#### Scenario: Descubrimiento sin novedades

- **WHEN** un `discover` termina sin registros nuevos
- **THEN** no se encola ningún enriquecimiento automático

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
