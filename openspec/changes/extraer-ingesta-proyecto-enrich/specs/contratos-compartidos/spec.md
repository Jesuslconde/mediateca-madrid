# Spec Delta

## Purpose

Definir un paquete compartido y versionado con los modelos de dominio y los contratos OpenAPI/JSON que consumen la ingesta, la API y el portal, para que las tres piezas evolucionen de forma coordinada.

## ADDED Requirements

### Requirement: Paquete compartido versionado

El sistema MUST publicar los modelos de dominio y los contratos como un paquete compartido con versionado semántico. La ingesta y la API SHALL fijar una versión concreta y MUST NOT depender de código no publicado.

#### Scenario: Consumo de una versión fija

- **WHEN** la API y la ingesta arrancan
- **THEN** ambas usan la misma versión declarada del paquete compartido
- **AND** la versión queda registrada en su configuración y en los logs de arranque

#### Scenario: Actualización coordinada

- **WHEN** se publica una nueva versión del paquete
- **THEN** cada consumidor actualiza su dependencia de forma explícita
- **AND** no se actualiza de forma automática sin revisión

### Requirement: Contrato OpenAPI/JSON para el portal

El paquete compartido MUST generar un contrato OpenAPI/JSON del catálogo y de la API pública. El portal SHALL generar sus tipos TypeScript desde ese contrato y MUST NOT mantener una copia manual divergente.

#### Scenario: Generación de tipos del portal

- **WHEN** se publica una versión nueva del contrato
- **THEN** el portal regenera sus tipos TypeScript
- **AND** la compilación falla si el contrato y el cliente no coinciden

#### Scenario: Contrato sin cambios incompatibles

- **WHEN** se añade un campo opcional al contrato
- **THEN** el portal sigue compilando sin cambios obligatorios
- **AND** los clientes antiguos siguen funcionando

### Requirement: Compatibilidad y evolución

Los cambios incompatibles del paquete compartido MUST incrementar la versión mayor y SHALL requerir un despliegue ordenado. La ingesta y la API SHALL validar al arrancar que la versión compartida es compatible con su esquema.

#### Scenario: Cambio incompatible

- **WHEN** se elimina o renombra un campo del modelo compartido
- **THEN** la versión mayor aumenta
- **AND** el despliegue se ordena shared, ingesta y API antes de retirar la versión anterior

#### Scenario: Versión incompatible en arranque

- **WHEN** un servicio arranca con una versión compartida incompatible
- **THEN** falla el arranque con un error legible
- **AND** no escribe datos con un esquema desconocido
