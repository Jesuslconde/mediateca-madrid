# estado-ingesta Specification

## Purpose

Persistir el estado de los trabajos de ingesta masiva y el progreso por edición para que descubrimiento, enriquecimiento e indexación sean reanudables, idempotentes y observables.

## Requirements

### Requirement: Trabajos de ingesta persistentes

El sistema MUST almacenar cada trabajo de ingesta con un identificador, tipo, fuente, estado, cursor, contadores y fechas de inicio y fin. La fuente SHALL quedar registrada en el trabajo y SHALL NOT cambiar durante su ejecución, salvo en el indexado global, que se registra explícitamente como global.

#### Scenario: Trabajo en curso

- **WHEN** el worker empieza un trabajo de enriquecimiento de una fuente
- **THEN** el trabajo queda en estado `running` con su fuente y su cursor inicial
- **AND** al terminar queda en `completed` o `failed` con estadísticas

#### Scenario: Reanudación tras un fallo

- **WHEN** un trabajo queda interrumpido
- **THEN** el siguiente worker puede reanudarlo desde el último cursor persistido de esa fuente
- **AND** no vuelve a procesar los registros ya completados

### Requirement: Marcas de progreso por edición

Cada edición MUST registrar cuándo fue descubierta y cuándo se enriqueció su ficha.

#### Scenario: Edición recién descubierta

- **WHEN** el descubrimiento encuentra un `TITN` nuevo
- **THEN** crea una edición stub con `discovery_seen_at`
- **AND** deja `detail_fetched_at` vacío hasta el enriquecimiento

#### Scenario: Edición enriquecida

- **WHEN** se procesa la ficha completa de un `TITN`
- **THEN** se actualiza `detail_fetched_at`
- **AND** la edición deja de considerarse stub

### Requirement: Cursores de descubrimiento

El descubrimiento MUST guardar el último `DOC` y el último `TITN` procesados de la fuente para poder continuar sin reiniciar la paginación. Los cursores SHALL ser independientes por fuente.

#### Scenario: Continuar descubrimiento

- **WHEN** se reanuda un descubrimiento interrumpido de una fuente
- **THEN** el cliente vuelve a ejecutar la búsqueda de esa fuente y salta al `DOC` guardado
- **AND** verifica que el primer `TITN` de la página coincide con el cursor

#### Scenario: Cursores de fuentes distintas

- **WHEN** dos fuentes tienen descubrimientos interrumpidos
- **THEN** cada una reanuda desde su propio `DOC` y `TITN`
- **AND** no se reutiliza el cursor de la otra

### Requirement: Idempotencia

Repetir un descubrimiento o un enriquecimiento MUST actualizar los registros existentes por la pareja `(fuente, titn)` sin crear duplicados. La misma pareja SHALL identificar siempre la misma edición.

#### Scenario: Reprocesar una edición

- **WHEN** se vuelve a enriquecer un `TITN` ya existente en la misma fuente
- **THEN** se actualizan sus datos y sus ejemplares
- **AND** no se crea una segunda edición con la misma pareja `(fuente, titn)`

#### Scenario: Mismo TITN en otra fuente

- **WHEN** se enriquece un `TITN` que ya existe en otra fuente
- **THEN** se crea o actualiza la edición de la fuente actual
- **AND** no se reutiliza ni se modifica la edición de la otra fuente

### Requirement: Consulta de estado

El sistema SHALL exponer el estado de los trabajos, los registros pendientes y la cobertura del catálogo desde CLI y API, con el desglose por fuente.

#### Scenario: Estado de la ingesta

- **WHEN** el operador consulta el estado
- **THEN** ve trabajos activos, completados y fallidos con su fuente
- **AND** ve cuántas ediciones están descubiertas, enriquecidas y pendientes por fuente

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

### Requirement: Cobertura por fuente

El sistema SHALL calcular y exponer la cobertura de descubrimiento y enriquecimiento de cada fuente de forma independiente, además del total agregado del catálogo.

#### Scenario: Cobertura de dos fuentes

- **WHEN** existen ediciones de dos fuentes con distinto grado de enriquecimiento
- **THEN** la cobertura muestra los conteos de cada fuente
- **AND** el total agregado coincide con la suma de las fuentes

#### Scenario: Fuente sin ediciones

- **WHEN** una fuente habilitada todavía no tiene ediciones
- **THEN** su cobertura muestra cero
- **AND** el porcentaje se calcula sin dividir por cero
