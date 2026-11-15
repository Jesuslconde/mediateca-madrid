# Spec Delta

## MODIFIED Requirements

### Requirement: Resumen de trabajos por estado y tipo

El sistema MUST mostrar el número de trabajos agrupados por estado (`pending`, `running`, `completed`, `failed`, `cancelled`) y por tipo (`discover`, `enrich`, `index`, `tmdb`).

#### Scenario: Conteo por estado

- **WHEN** existen trabajos en varios estados
- **THEN** la vista muestra el total de cada estado
- **AND** los estados sin trabajos se muestran con valor cero

#### Scenario: Conteo por tipo

- **WHEN** existen trabajos de descubrimiento, enriquecimiento, indexación y actualización TMDB
- **THEN** la vista muestra el total de cada tipo
- **AND** los tipos sin trabajos se muestran con valor cero

### Requirement: Tareas bajo demanda

El dashboard MUST permitir encolar descubrimiento incremental, descubrimiento completo, enriquecimiento, indexación y actualización de metadatos TMDB, y SHALL rechazar la acción si ya existe un trabajo activo del mismo tipo. La actualización TMDB SHALL permitir elegir el lote y reactualizar también las ediciones ya sincronizadas, y MUST rechazarse si no hay token de TMDB configurado.

#### Scenario: Buscar novedades

- **WHEN** el operador pulsa "Buscar novedades"
- **THEN** se encola un `discover` incremental con el cursor del último descubrimiento completado
- **AND** el worker lo procesa cuando esté libre

#### Scenario: Enriquecer pendientes

- **WHEN** el operador pulsa "Enriquecer pendientes"
- **THEN** se encola un `enrich` con el lote indicado
- **AND** se procesan todos los stubs pendientes, no solo los de la última búsqueda

#### Scenario: Actualizar metadatos TMDB

- **WHEN** el operador pulsa "Actualizar metadatos TMDB" con un lote y, opcionalmente, la casilla de refresco
- **THEN** se encola un trabajo `tmdb` con el lote y el modo indicados
- **AND** el trabajo se ejecuta en el worker y queda registrado en el historial

#### Scenario: Actualización TMDB sin token

- **WHEN** el operador solicita una actualización TMDB sin un token configurado
- **THEN** el dashboard muestra un error comprensible
- **AND** no se crea ningún trabajo

#### Scenario: Trabajo duplicado

- **WHEN** ya hay un trabajo `pending` o `running` del mismo tipo
- **THEN** el dashboard muestra un error comprensible
- **AND** no crea otro trabajo

### Requirement: Página de Tareas

La página de Tareas MUST mostrar los trabajos recientes y las acciones de descubrimiento, enriquecimiento, indexación y actualización de metadatos TMDB. SHALL conservar las reglas de encolado, la desactivación de acciones con un trabajo activo y la protección de escritura.

#### Scenario: Visualización de trabajos

- **WHEN** el operador abre `/tareas`
- **THEN** ve la tabla de trabajos recientes con los mismos campos y orden que antes
- **AND** ve el estado activo de cada tipo de trabajo

#### Scenario: Acciones bajo demanda

- **WHEN** el operador pulsa una acción de descubrimiento, enriquecimiento, indexación o actualización TMDB
- **THEN** se encola el trabajo con las mismas reglas que en la vista anterior
- **AND** las acciones con un trabajo activo del mismo tipo siguen deshabilitadas

#### Scenario: Redirección con mensaje

- **WHEN** una acción de tareas termina con éxito o error
- **THEN** el operador vuelve a `/tareas`
- **AND** ve el mensaje correspondiente en esa página

#### Scenario: Escritura sin administración

- **WHEN** el operador no tiene sesión de administración y hay token configurado
- **THEN** las acciones de encolado aparecen deshabilitadas o se rechazan
- **AND** no se crea ningún trabajo
