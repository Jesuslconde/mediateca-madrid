# Spec Delta

## ADDED Requirements

### Requirement: Estado de enriquecimiento OPAC por edición

Cada edición MUST conservar el estado de su enriquecimiento OPAC con `enrich_status` (`pending`, `enriched`, `failed`), `enrich_attempts`, `enrich_last_attempt_at` y `enrich_last_error`. Un intento fallido SHALL incrementar los intentos y guardar el error sin borrar una ficha ya enriquecida.

#### Scenario: Ficha enriquecida

- **WHEN** se descarga y guarda la ficha OPAC de una edición
- **THEN** `enrich_status` pasa a `enriched`
- **AND** `detail_fetched_at` registra la fecha de la última ficha correcta
- **AND** `enrich_last_error` queda vacío

#### Scenario: Intento fallido

- **WHEN** la descarga de la ficha falla tras los reintentos
- **THEN** `enrich_status` pasa a `failed`
- **AND** `enrich_attempts` se incrementa
- **AND** `enrich_last_error` guarda el motivo y `enrich_last_attempt_at` la fecha

#### Scenario: Fallo repetido

- **WHEN** una edición vuelve a fallar en un lote posterior
- **THEN** `enrich_attempts` sigue acumulando
- **AND** `enrich_last_attempt_at` y `enrich_last_error` reflejan el último intento

#### Scenario: Éxito tras un fallo

- **WHEN** una edición fallida se enriquece correctamente más adelante
- **THEN** `enrich_status` pasa a `enriched`
- **AND** se conserva el número de intentos
- **AND** `enrich_last_error` queda vacío

#### Scenario: Edición histórica

- **WHEN** una edición ya existía antes de este cambio
- **THEN** su estado inicial es `enriched` si tiene `detail_fetched_at`
- **AND** es `pending` en caso contrario
