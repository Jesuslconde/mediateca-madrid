# Spec Delta

## ADDED Requirements

### Requirement: Alta de la fuente Andalucía

La migración de despliegue MUST crear de forma idempotente la fuente `andalucia` con su perfil OPAC y estado habilitado. El alta SHALL NOT cambiar la identidad de las ediciones existentes ni exigir un reindexado de Madrid.

#### Scenario: Migración sobre una instalación existente

- **WHEN** se ejecuta la migración de Andalucía sobre una base con Madrid
- **THEN** se crea la fila `andalucia` en `fuentes`
- **AND** las ediciones, bibliotecas, ejemplares y trabajos de Madrid permanecen intactos

#### Scenario: Migración repetida

- **WHEN** la migración se ejecuta de nuevo
- **THEN** termina sin errores
- **AND** el número de filas de `andalucia` no aumenta

#### Scenario: Despliegue con la fuente habilitada

- **WHEN** `init` arranca con la migración ya aplicada
- **THEN** `andalucia` sigue habilitada y disponible para el scheduler
- **AND** `init` no reconstruye el índice de Madrid por este alta
