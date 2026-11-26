# Spec Delta

## ADDED Requirements

### Requirement: Parámetros de proximidad en la búsqueda

`GET /api/search` SHALL aceptar `cp` (código postal de cinco dígitos), `radio_km` (número positivo) y `excluir` (repetible, códigos de ubicación). `radio_km` SHALL requerir un `cp` resoluble. La API SHALL devolver 422 cuando `radio_km` se envíe sin `cp` o con un `cp` no resoluble.

#### Scenario: Búsqueda acotada por radio

- **WHEN** el cliente solicita `/api/search?cp=28015&radio_km=5`
- **THEN** recibe solo las ediciones con ejemplares en sucursales dentro de 5 km
- **AND** los totales y las facetas se calculan sobre ese conjunto

#### Scenario: Radio sin código postal

- **WHEN** el cliente solicita `/api/search?radio_km=5` sin `cp`
- **THEN** la API responde con 422
- **AND** indica que `radio_km` requiere `cp`

#### Scenario: Código postal no resoluble

- **WHEN** el cliente solicita `/api/search?cp=00000&radio_km=5`
- **THEN** la API responde con 422
- **AND** indica que el código postal no se puede resolver

#### Scenario: Código postal sin radio

- **WHEN** el cliente solicita `/api/search?cp=28015` sin `radio_km`
- **THEN** la búsqueda no se acota por distancia
- **AND** se comporta como una búsqueda sin proximidad

#### Scenario: Excluir ubicaciones

- **WHEN** el cliente solicita `/api/search?cp=28015&radio_km=5&excluir=s:madrid:BMALC1`
- **THEN** se excluyen las ediciones que solo tienen ejemplares en esa sucursal
- **AND** el resto de la búsqueda se mantiene

### Requirement: Ubicaciones con coordenadas y distancia

`GET /api/locations` SHALL incluir por ubicación su código postal, latitud y longitud cuando estén disponibles. SHALL aceptar `cp` y `radio_km` opcionales para devolver solo las ubicaciones cercanas, con su distancia aproximada en kilómetros.

#### Scenario: Listado con coordenadas

- **WHEN** el cliente solicita `/api/locations`
- **THEN** cada ubicación incluye su código postal, latitud y longitud cuando estén disponibles
- **AND** los campos de ubicación son opcionales

#### Scenario: Ubicaciones cercanas

- **WHEN** el cliente solicita `/api/locations?cp=28015&radio_km=5`
- **THEN** recibe solo las ubicaciones dentro de 5 km
- **AND** cada una incluye su distancia aproximada en kilómetros
- **AND** se ordenan de menor a mayor distancia

#### Scenario: Distancia sin referencia

- **WHEN** el cliente solicita `/api/locations` sin `cp` ni `radio_km`
- **THEN** las ubicaciones no incluyen distancia
- **AND** se mantienen el orden y los campos anteriores
