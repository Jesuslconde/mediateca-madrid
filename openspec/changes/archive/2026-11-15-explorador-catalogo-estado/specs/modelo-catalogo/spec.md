# Spec Delta

## ADDED Requirements

### Requirement: Columnas de estado de enriquecimiento

Cada edición MUST almacenar el estado de enriquecimiento OPAC y TMDB con las columnas `enrich_status`, `enrich_attempts`, `enrich_last_attempt_at`, `enrich_last_error`, `tmdb_status`, `tmdb_attempts`, `tmdb_last_attempt_at` y `tmdb_last_error`. La migración SHALL ser idempotente y `SCHEMA_VERSION` SHALL pasar a `4`.

#### Scenario: Migración idempotente

- **WHEN** se aplica la migración sobre una base con o sin las columnas
- **THEN** las columnas quedan creadas una sola vez
- **AND** `schema_meta.schema_version` queda en `4`

#### Scenario: Valores por defecto

- **WHEN** se crea una edición nueva
- **THEN** `enrich_status` y `tmdb_status` valen `pending`
- **AND** los contadores de intentos valen `0`

#### Scenario: Ediciones existentes

- **WHEN** la migración se aplica sobre ediciones ya enriquecidas
- **THEN** `enrich_status` queda en `enriched`
- **AND** `tmdb_status` queda en `matched` si tienen `tmdb_enriched_at`
- **AND** el resto queda en `pending`
