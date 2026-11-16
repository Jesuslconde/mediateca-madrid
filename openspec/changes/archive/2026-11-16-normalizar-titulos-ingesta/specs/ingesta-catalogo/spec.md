# Spec Delta

## MODIFIED Requirements

### Requirement: Parser de listado de resultados

El recolector MUST extraer de cada resultado el `TITN`, título, publicación, año, idioma, descripción física, géneros, materias y, cuando existan, autores y notas del MARC oculto. El título MUST ser el título propio visible, sin la mención de responsabilidad.

#### Scenario: Resultado con MARC oculto

- **WHEN** se parsea un `li.c-docs_unit`
- **THEN** se obtiene al menos `TITN`, título y descripción física
- **AND** se detecta el soporte desde `T300a`

#### Scenario: Título con mención de responsabilidad

- **WHEN** el resultado muestra `20.000 especies de abejas / dirección y guión de Estibaliz Urresola`
- **THEN** la edición guarda `20.000 especies de abejas`
- **AND** la mención de responsabilidad no forma parte del título

#### Scenario: Título con subtítulo en el listado

- **WHEN** el resultado muestra `Imágenes y justicia : el Derecho a través del cine /`
- **THEN** la edición guarda `Imágenes y justicia : el Derecho a través del cine`

## ADDED Requirements

### Requirement: Backfill de títulos normalizados

El sistema SHALL ofrecer un comando idempotente que recalcule los títulos de las ediciones existentes a partir de los metadatos MARC ya guardados, sin recolectar de nuevo el OPAC ni modificar las claves de agrupación de obras.

#### Scenario: Backfill en seco

- **WHEN** el operador ejecuta el backfill sin aplicar cambios
- **THEN** el comando informa de cuántas ediciones cambiarían y muestra ejemplos
- **AND** no modifica la base de datos

#### Scenario: Backfill aplicado

- **WHEN** el operador aplica el backfill
- **THEN** se actualizan `titulo` y `titulo_uniforme` de las ediciones afectadas
- **AND** no se crean ni modifican obras ni ejemplares

#### Scenario: Backfill idempotente

- **WHEN** el backfill se ejecuta dos veces seguidas
- **THEN** la segunda ejecución no encuentra títulos que cambiar

#### Scenario: Backfill con reindexado

- **WHEN** el operador aplica el backfill y solicita reindexar
- **THEN** las ediciones afectadas se envían al índice
- **AND** el resto del índice permanece intacto
