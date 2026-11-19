# cola-trabajos Specification

## Purpose

Ejecutar trabajos de ingesta largos y reanudables fuera del scheduler, con una cola persistente en PostgreSQL y un worker que procesa varios trabajos compatibles a la vez.

## Requirements

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

El sistema MUST NOT encolar trabajos de tipo `branches` desde el scheduler. El trabajo `branches` SHALL crearse solo por una acción explícita del operador desde el dashboard o la CLI y SHALL respetar la política de directorio de la fuente: con `match` SHALL procesar únicamente bibliotecas que ya existan en el catálogo, y con `create` SHALL poder crear bibliotecas y sucursales desde el directorio. En ningún caso SHALL crear ediciones ni ejemplares.

#### Scenario: Scheduler sin recarga de bibliotecas

- **WHEN** el scheduler comprueba los intervalos configurados
- **THEN** no crea ningún trabajo de tipo `branches`
- **AND** solo puede encolar `discover`, `enrich` e `index`

#### Scenario: Recarga solo de bibliotecas conocidas

- **WHEN** el operador lanza una recarga de bibliotecas sobre una fuente con política `match`
- **THEN** se crea un trabajo `branches` en estado `pending`
- **AND** el trabajo omite las fichas de bibliotecas que no existan previamente
- **AND** crea o actualiza las sucursales de las bibliotecas conocidas
- **AND** no crea bibliotecas nuevas

#### Scenario: Recarga con política create

- **WHEN** el operador lanza una recarga de bibliotecas sobre una fuente con política `create`
- **THEN** se crea un trabajo `branches` en estado `pending`
- **AND** el trabajo crea las bibliotecas y sucursales que falten a partir del directorio
- **AND** actualiza las que ya existan
- **AND** no crea ediciones ni ejemplares
