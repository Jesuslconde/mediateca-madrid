# Spec Delta

## ADDED Requirements

### Requirement: Modelo compartido y versión única

El modelo de datos MUST definirse en el paquete compartido. La ingesta y la API SHALL usar la misma versión del modelo, y solo la ingesta SHALL aplicar migraciones o escribir en las tablas del catálogo.

#### Scenario: Misma versión en ingesta y API

- **WHEN** la ingesta y la API arrancan
- **THEN** ambas declaran la misma versión del modelo compartido
- **AND** rechazan arrancar con una versión incompatible

#### Scenario: Lectura con modelo compartido

- **WHEN** la API consulta obras, ediciones o ejemplares
- **THEN** usa el modelo compartido en modo lectura
- **AND** no crea ni modifica tablas ni registros

#### Scenario: Migración desde la ingesta

- **WHEN** cambia el esquema del catálogo
- **THEN** la migración se aplica desde `mediateca-madrid-enrich`
- **AND** la API solo consume el esquema resultante
