# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
