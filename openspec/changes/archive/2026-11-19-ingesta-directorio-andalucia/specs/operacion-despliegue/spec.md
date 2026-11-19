# Spec Delta

## ADDED Requirements

### Requirement: Directorio abierto de Andalucía en la migración

La migración de despliegue MUST configurar de forma idempotente el directorio abierto de la fuente `andalucia` en `fuentes.options`, con tipo `opendata`, URL del conjunto de datos, política `create` y filtro por defecto de tipo `Biblioteca`. El cambio SHALL NOT alterar el perfil OPAC de Andalucía ni los datos de Madrid.

#### Scenario: Configuración sobre una instalación existente

- **WHEN** se ejecuta la migración del directorio sobre una base con la fuente `andalucia`
- **THEN** `fuentes.options` de `andalucia` declara el directorio `opendata`
- **AND** el perfil OPAC, la identidad de las ediciones y los datos de Madrid permanecen intactos

#### Scenario: Migración repetida

- **WHEN** la migración se ejecuta de nuevo
- **THEN** termina sin errores
- **AND** no duplica ni corrompe la configuración del directorio

#### Scenario: Despliegue sin reindexado

- **WHEN** `init` arranca con la migración aplicada
- **THEN** no se reconstruye el índice por este cambio
- **AND** la fuente queda disponible para la actualización manual del directorio
