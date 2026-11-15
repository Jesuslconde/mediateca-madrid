# Spec Delta

## MODIFIED Requirements

### Requirement: Encolado de trabajos

El sistema MUST permitir encolar trabajos de tipo `discover`, `enrich`, `index` y `tmdb` con un lote y un cursor inicial desde la CLI o el dashboard. El scheduler SHALL limitarse a encolar `discover`, `enrich` e `index`.

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

## ADDED Requirements

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
