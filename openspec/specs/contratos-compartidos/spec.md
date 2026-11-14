# contratos-compartidos Specification

## Purpose

Definir una unica fuente de modelos de dominio y contratos OpenAPI/JSON dentro del monorepo, consumida por la ingesta, la API y el portal, para que las piezas evolucionen en el mismo commit.

## Requirements

### Requirement: Paquete compartido local

El sistema MUST mantener los modelos de dominio y los contratos en `packages/shared`. La ingesta y la API SHALL instalar ese paquete desde la ruta local y MUST NOT depender de wheels, copias locales ni repositorios separados.

#### Scenario: Consumo del paquete local

- **WHEN** se construyen las imagenes `mediateca-batch` y `mediateca-web`
- **THEN** ambas instalan `packages/shared` en el mismo commit
- **AND** no descargan ninguna version publicada de `mediateca-shared`

#### Scenario: Actualizacion coordinada

- **WHEN** cambia un modelo o un esquema
- **THEN** el cambio se aplica en `packages/shared`
- **AND** la migracion correspondiente se aplica en `services/enrich` en el mismo commit
- **AND** no hay que publicar ni sincronizar wheels entre repositorios

### Requirement: Contrato OpenAPI/JSON unico

La API MUST generar el contrato OpenAPI/JSON en `contracts/openapi.json`. El portal SHALL generar sus tipos TypeScript desde ese contrato y MUST NOT mantener una copia manual divergente.

#### Scenario: Generacion de tipos del portal

- **WHEN** se ejecuta `make contracts`
- **THEN** se actualiza `contracts/openapi.json`
- **AND** el portal regenera `apps/web/lib/api-types.ts`
- **AND** la compilacion falla si el contrato y el cliente no coinciden

#### Scenario: Contrato sin cambios incompatibles

- **WHEN** se anade un campo opcional al contrato
- **THEN** el portal sigue compilando sin cambios obligatorios
- **AND** los clientes antiguos siguen funcionando

### Requirement: Compatibilidad y evolucion

Los cambios incompatibles del modelo compartido MUST incrementar `SCHEMA_VERSION` y SHALL requerir un despliegue coordinado. La API SHALL validar al arrancar que el esquema de la base de datos coincide con `SCHEMA_VERSION`.

#### Scenario: Cambio incompatible

- **WHEN** se elimina o renombra un campo del modelo compartido
- **THEN** `SCHEMA_VERSION` aumenta
- **AND** `init` aplica la migracion antes de arrancar la API
- **AND** las dos imagenes se reconstruyen desde el mismo commit

#### Scenario: Version incompatible en arranque

- **WHEN** un servicio arranca con un esquema incompatible
- **THEN** falla el arranque con un error legible
- **AND** no escribe datos con un esquema desconocido
