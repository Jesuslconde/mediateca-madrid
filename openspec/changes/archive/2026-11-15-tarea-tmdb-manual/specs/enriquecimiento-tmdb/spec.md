# Spec Delta

## MODIFIED Requirements

### Requirement: Backfill manual

El sistema SHALL ofrecer un comando y una tarea manual de cola que enriquezcan con TMDB las ediciones pendientes, por lotes y con reanudación, sin reprocesar por defecto las ya sincronizadas. Ambos SHALL permitir un modo de refresco que reconsulte TMDB también para las ediciones ya sincronizadas.

#### Scenario: Lote de backfill

- **WHEN** el operador ejecuta el backfill con un límite de lote
- **THEN** se procesan hasta ese número de ediciones sin `tmdb_enriched_at`
- **AND** al terminar se informa del número de procesadas, emparejadas, sin coincidencia y fallidas

#### Scenario: Reanudación del backfill

- **WHEN** el backfill se interrumpe a mitad de un lote
- **THEN** la siguiente ejecución continúa por las ediciones que siguen pendientes
- **AND** no repite las ya sincronizadas

#### Scenario: Backfill sin token

- **WHEN** el operador ejecuta el backfill sin un token de TMDB configurado
- **THEN** el comando o la tarea terminan con un error legible
- **AND** no se modifica ninguna edición

#### Scenario: Tarea manual desde el dashboard

- **WHEN** el operador lanza la actualización TMDB desde el dashboard con un lote
- **THEN** se crea un trabajo `tmdb` que el worker ejecuta de forma manual
- **AND** al terminar se indexan los TITN procesados

#### Scenario: Refresco de ediciones sincronizadas

- **WHEN** el operador activa el modo de refresco
- **THEN** se reconsultan también las ediciones que ya tienen `tmdb_enriched_at`
- **AND** se actualizan portada, enlace, países e identificador con el resultado actual
- **AND** las ediciones se ordenan por sincronización más antigua para rotar los lotes

#### Scenario: Refresco sin coincidencia

- **WHEN** una edición ya sincronizada no obtiene coincidencia en una nueva consulta
- **THEN** se conservan los metadatos TMDB anteriores
- **AND** la edición no se marca con una nueva fecha de sincronización
