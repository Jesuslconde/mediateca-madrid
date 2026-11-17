# cola-trabajos Specification

## Purpose

Ejecutar trabajos de ingesta largos y reanudables fuera del scheduler, con una cola persistente en PostgreSQL y un worker que procesa varios trabajos compatibles a la vez.

## Requirements

### Requirement: Encolado de trabajos

El sistema MUST permitir encolar trabajos de tipo `discover`, `enrich`, `index`, `tmdb` y `branches` con un lote y un cursor inicial desde la CLI o el dashboard. El scheduler SHALL limitarse a encolar `discover`, `enrich` e `index`; `tmdb` y `branches` SHALL ser siempre manuales.

#### Scenario: Encolar enriquecimiento

- **WHEN** el scheduler encola un trabajo de enriquecimiento de 5.000 fichas
- **THEN** el trabajo queda en estado `pending`
- **AND** el worker puede reclamarlo

#### Scenario: Encolar desde el dashboard

- **WHEN** el operador solicita un trabajo bajo demanda
- **THEN** se crea un trabajo `pending` con el tipo y lote solicitados
- **AND** el dashboard no ejecuta la ingesta

#### Scenario: Encolar actualización TMDB

- **WHEN** el operador solicita una actualización de metadatos TMDB desde el dashboard
- **THEN** se crea un trabajo `pending` de tipo `tmdb` con el lote y el modo de refresco indicados
- **AND** el worker lo ejecuta cuando esté libre

#### Scenario: Encolar recarga de bibliotecas

- **WHEN** el operador solicita una recarga de direcciones de bibliotecas desde el dashboard o la CLI
- **THEN** se crea un trabajo `pending` de tipo `branches`
- **AND** el worker lo ejecuta cuando esté libre

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

### Requirement: Concurrencia configurable

El sistema SHALL permitir ejecutar varios trabajos a la vez, con un máximo de cinco (uno por tipo), configurable entre 1 y 5 por variable de entorno, CLI o dashboard. El dashboard SHALL guardar el valor en `app_config` y SHALL prevalecer sobre el entorno; el worker SHALL aplicarlo al arrancar.

#### Scenario: Tareas compatibles

- **WHEN** hay un `discover` en ejecución y se encola `branches`
- **THEN** `branches` se reclama y ejecuta en paralelo
- **AND** cada trabajo mantiene su propio heartbeat y checkpoint

#### Scenario: Concurrencia configurable

- **WHEN** se configura una concurrencia de 3
- **THEN** el worker arranca tres hilos de reclamo
- **AND** nunca supera las reglas de exclusión por tipo y dependencia

#### Scenario: Configuración desde el dashboard

- **WHEN** el operador guarda la concurrencia en el dashboard
- **THEN** el valor queda en `app_config`
- **AND** se aplica cuando el worker se reinicia

### Requirement: Exclusión por tipo y dependencia

El sistema MUST NOT ejecutar dos trabajos del mismo tipo ni las parejas con dependencia `discover`/`enrich`, `enrich`/`tmdb`, `enrich`/`index` ni `tmdb`/`index`. `branches` SHALL ser compatible con todos. El reclamo SHALL serializarse en PostgreSQL para respetar las reglas entre hilos y contenedores.

#### Scenario: Dependencia activa

- **WHEN** hay un `discover` en ejecución y se encola `enrich`
- **THEN** `enrich` permanece `pending`
- **AND** se ejecuta cuando termina el `discover`

#### Scenario: Mismo tipo activo

- **WHEN** hay un `enrich` en ejecución y existe otro `enrich` pendiente
- **THEN** el worker no reclama el segundo
- **AND** lo deja esperando al primero


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

### Requirement: Tarea TMDB solo manual

El sistema MUST NOT encolar trabajos de tipo `tmdb` desde el scheduler. El trabajo `tmdb` SHALL crearse solo por una acción explícita del operador desde el dashboard o la CLI.

#### Scenario: Scheduler sin tarea TMDB

- **WHEN** el scheduler comprueba los intervalos configurados
- **THEN** no crea ningún trabajo de tipo `tmdb`
- **AND** solo puede encolar `discover`, `enrich` e `index`

#### Scenario: Lanzamiento explícito

- **WHEN** no hay ningún trabajo `tmdb` activo y el operador lo solicita manualmente
- **THEN** se crea un trabajo `tmdb` en estado `pending`
- **AND** no se crea ningún otro trabajo `tmdb` mientras siga activo

### Requirement: Recarga de bibliotecas solo manual

El sistema MUST NOT encolar trabajos de tipo `branches` desde el scheduler. El trabajo `branches` SHALL crearse solo por una acción explícita del operador desde el dashboard o la CLI y SHALL procesar únicamente bibliotecas que ya existan en el catálogo, creando o actualizando sus sucursales sin crear bibliotecas nuevas.

#### Scenario: Scheduler sin recarga de bibliotecas

- **WHEN** el scheduler comprueba los intervalos configurados
- **THEN** no crea ningún trabajo de tipo `branches`
- **AND** solo puede encolar `discover`, `enrich` e `index`

#### Scenario: Recarga solo de bibliotecas conocidas

- **WHEN** el operador lanza una recarga de bibliotecas
- **THEN** se crea un trabajo `branches` en estado `pending`
- **AND** el trabajo omite las fichas de bibliotecas que no existan previamente
- **AND** crea o actualiza las sucursales de las bibliotecas conocidas
- **AND** no crea bibliotecas nuevas
