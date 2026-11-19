# Spec Delta

## MODIFIED Requirements

### Requirement: Recarga de bibliotecas solo manual

El sistema MUST NOT encolar trabajos de tipo `branches` desde el scheduler. El trabajo `branches` SHALL crearse solo por una acción explícita del operador desde el dashboard o la CLI y SHALL respetar la política de directorio de la fuente: con `match` SHALL procesar únicamente bibliotecas que ya existan en el catálogo, y con `create` SHALL poder crear bibliotecas y sucursales desde el directorio. En ningún caso SHALL crear ediciones ni ejemplares.

#### Scenario: Scheduler sin recarga de bibliotecas

- **WHEN** el scheduler comprueba los intervalos configurados
- **THEN** no crea ningún trabajo de tipo `branches`
- **AND** solo puede encolar `discover`, `enrich` e `index`

#### Scenario: Recarga solo de bibliotecas conocidas

- **WHEN** el operador lanza una recarga de bibliotecas sobre una fuente con política `match`
- **THEN** se crea un trabajo `branches` en estado `pending`
- **AND** el trabajo omite las fichas de bibliotecas que no existan previamente
- **AND** crea o actualiza las sucursales de las bibliotecas conocidas
- **AND** no crea bibliotecas nuevas

#### Scenario: Recarga con política create

- **WHEN** el operador lanza una recarga de bibliotecas sobre una fuente con política `create`
- **THEN** se crea un trabajo `branches` en estado `pending`
- **AND** el trabajo crea las bibliotecas y sucursales que falten a partir del directorio
- **AND** actualiza las que ya existan
- **AND** no crea ediciones ni ejemplares
