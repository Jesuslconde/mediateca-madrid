# Spec Delta

## ADDED Requirements

### Requirement: Estado del emparejamiento TMDB por edición

Cada edición MUST conservar el resultado de su enriquecimiento TMDB con `tmdb_status` (`pending`, `matched`, `unmatched`, `error`, `skipped`), `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error`. `tmdb_enriched_at` SHALL registrar solo la última coincidencia correcta.

#### Scenario: Coincidencia correcta

- **WHEN** TMDB devuelve una película fiable
- **THEN** `tmdb_status` pasa a `matched`
- **AND** se actualizan `tmdb_id`, `paises_origen` y `tmdb_enriched_at`
- **AND** `tmdb_last_error` queda vacío

#### Scenario: Sin coincidencia

- **WHEN** TMDB no devuelve una coincidencia fiable
- **THEN** `tmdb_status` pasa a `unmatched`
- **AND** `tmdb_enriched_at` no se actualiza
- **AND** el resultado deja de ser indistinguible de un pendiente

#### Scenario: Error temporal

- **WHEN** la consulta a TMDB falla tras los reintentos
- **THEN** `tmdb_status` pasa a `error`
- **AND** `tmdb_attempts` se incrementa y `tmdb_last_error` guarda el motivo
- **AND** no se borran `paises_origen` ni `tmdb_id` previos

#### Scenario: Sin token

- **WHEN** no hay token de TMDB configurado
- **THEN** `tmdb_status` pasa a `skipped`
- **AND** no se registra un error por la ausencia de token

#### Scenario: Reintento posterior

- **WHEN** una edición con estado `unmatched` o `error` se vuelve a procesar
- **THEN** `tmdb_attempts` se incrementa
- **AND** el estado se actualiza con el nuevo resultado
