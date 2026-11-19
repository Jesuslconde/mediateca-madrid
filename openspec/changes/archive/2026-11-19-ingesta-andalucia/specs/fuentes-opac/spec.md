# Spec Delta

## ADDED Requirements

### Requirement: Fuente Andalucía operativa

El sistema SHALL registrar la fuente `andalucia` con perfil AbsysNet, estado habilitado y filtro de formato `Videograbaciones` (`select03=05`). La fuente SHALL poder ejecutar descubrimiento, enriquecimiento e indexado sin compartir sesión ni contadores con Madrid.

#### Scenario: Semilla de Andalucía

- **WHEN** se aplica la migración de la fuente sobre una base que ya contiene Madrid
- **THEN** existe la fuente `andalucia` habilitada con su perfil OPAC
- **AND** la fuente y el catálogo de Madrid no se modifican

#### Scenario: Reejecución de la semilla

- **WHEN** la migración de Andalucía se ejecuta por segunda vez
- **THEN** no se crea una fuente duplicada
- **AND** no se altera el perfil existente

#### Scenario: Tareas de Andalucía

- **WHEN** el scheduler evalúa las fuentes habilitadas
- **THEN** puede encolar trabajos para `andalucia`
- **AND** los trabajos de Madrid conservan su propia fuente y su propio cursor

#### Scenario: Misma TITN en dos fuentes

- **WHEN** Madrid y Andalucía tienen una edición con la misma `TITN`
- **THEN** existen dos ediciones con `record_id` distintos
- **AND** cada una conserva su fuente y sus propios ejemplares

#### Scenario: Ejecución desde la CLI

- **WHEN** el operador ejecuta `discover --fuente andalucia`
- **THEN** la recolección usa el perfil de Andalucía
- **AND** no reutiliza la sesión ni el filtro de Madrid
