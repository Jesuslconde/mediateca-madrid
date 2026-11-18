# Spec Delta

## MODIFIED Requirements

### Requirement: Encolado de trabajos

El sistema MUST permitir encolar trabajos de tipo `discover`, `enrich`, `index`, `tmdb` y `branches` con una fuente, un lote y un cursor inicial desde la CLI o el dashboard. El scheduler SHALL limitarse a encolar `discover`, `enrich` e `index`; `tmdb` y `branches` SHALL ser siempre manuales. Todo trabajo SHALL declarar la fuente sobre la que opera, salvo el indexado global, que SHALL declararse explícitamente como global.

#### Scenario: Encolar enriquecimiento

- **WHEN** el scheduler encola un trabajo de enriquecimiento de 5.000 fichas para una fuente
- **THEN** el trabajo queda en estado `pending` con esa fuente
- **AND** el worker puede reclamarlo

#### Scenario: Encolar desde el dashboard

- **WHEN** el operador solicita un trabajo bajo demanda
- **THEN** se crea un trabajo `pending` con el tipo, la fuente y el lote solicitados
- **AND** el dashboard no ejecuta la ingesta

#### Scenario: Encolar actualización TMDB

- **WHEN** el operador solicita una actualización de metadatos TMDB desde el dashboard
- **THEN** se crea un trabajo `pending` de tipo `tmdb` con la fuente, el lote y el modo de refresco indicados
- **AND** el worker lo ejecuta cuando esté libre

#### Scenario: Encolar recarga de bibliotecas

- **WHEN** el operador solicita una recarga de direcciones de bibliotecas desde el dashboard o la CLI
- **THEN** se crea un trabajo `pending` de tipo `branches` con la fuente indicada
- **AND** el worker lo ejecuta cuando esté libre

#### Scenario: Encolar un indexado global

- **WHEN** el operador solicita una reconstrucción completa del índice
- **THEN** se crea un trabajo `index` marcado como global
- **AND** el trabajo no se limita a una fuente

### Requirement: Exclusión por tipo y dependencia

El sistema MUST NOT ejecutar dos trabajos del mismo tipo para la misma fuente ni las parejas con dependencia `discover`/`enrich`, `enrich`/`tmdb`, `enrich`/`index` ni `tmdb`/`index` dentro de una fuente. `branches` SHALL ser compatible con todos. Dos fuentes distintas SHALL poder ejecutar trabajos del mismo tipo salvo que un indexado global esté activo. El reclamo SHALL serializarse en PostgreSQL para respetar las reglas entre hilos y contenedores.

#### Scenario: Dependencia activa

- **WHEN** hay un `discover` en ejecución para una fuente y se encola un `enrich` para esa misma fuente
- **THEN** `enrich` permanece `pending`
- **AND** se ejecuta cuando termina el `discover`

#### Scenario: Mismo tipo activo

- **WHEN** hay un `enrich` en ejecución para una fuente y existe otro `enrich` pendiente para esa fuente
- **THEN** el worker no reclama el segundo
- **AND** lo deja esperando al primero

#### Scenario: Trabajos de fuentes distintas

- **WHEN** hay un `enrich` en ejecución para una fuente y se encola un `enrich` para otra fuente
- **THEN** el segundo puede reclamarse y ejecutarse en paralelo
- **AND** cada uno mantiene su sesión y su cursor

#### Scenario: Indexado global activo

- **WHEN** hay un indexado global en ejecución
- **THEN** no se reclama ningún trabajo de ingesta de ninguna fuente
- **AND** los trabajos permanecen `pending` hasta que termine

### Requirement: Deduplicación de trabajos

El sistema MUST impedir que existan dos trabajos activos del mismo tipo y la misma fuente, y SHALL devolver un error comprensible cuando se intente encolar un duplicado. Un trabajo del mismo tipo para otra fuente SHALL considerarse distinto.

#### Scenario: Duplicado activo

- **WHEN** ya hay un `discover`, `enrich` o `index` en estado `pending` o `running` para una fuente
- **THEN** un nuevo encolado del mismo tipo y fuente se rechaza
- **AND** el trabajo existente no se modifica

#### Scenario: Misma tarea en otra fuente

- **WHEN** ya hay un `discover` activo para una fuente
- **THEN** se puede encolar un `discover` para otra fuente
- **AND** ambos conservan su propio estado y cursor

### Requirement: Programación periódica

El scheduler MUST recorrer las fuentes habilitadas, encolar sus trabajos programados sin ejecutar el OPAC y SHALL leer la configuración desde `app_config` en cada comprobación. Los intervalos y las decisiones de encolado SHALL evaluarse por fuente.

#### Scenario: Descubrimiento programado

- **WHEN** se cumple el intervalo de descubrimiento de una fuente habilitada
- **THEN** el scheduler encola un `discover` incremental para esa fuente
- **AND** no encola otro para la misma fuente si ya hay uno activo

#### Scenario: Barrido completo programado

- **WHEN** se cumple el intervalo de barrido completo de una fuente
- **THEN** el scheduler encola un `discover` completo para esa fuente
- **AND** el modo queda registrado en las estadísticas del trabajo

#### Scenario: Enriquecimiento programado

- **WHEN** existen ediciones pendientes de ficha OPAC en una fuente y se cumple su intervalo de enriquecimiento
- **THEN** el scheduler encola un `enrich` para esa fuente sobre todos sus pendientes
- **AND** no encola otro para esa fuente si ya hay un descubrimiento o enriquecimiento activo

#### Scenario: Fuente deshabilitada

- **WHEN** una fuente está deshabilitada
- **THEN** el scheduler no encola ningún trabajo para ella
- **AND** las demás fuentes siguen su programación normal
