# Spec Delta

## ADDED Requirements

### Requirement: Ubicación de ejemplares en la ficha

La respuesta de `GET /api/records/{titn}` SHALL incluir por ejemplar una `ubicacion` opcional con código postal, municipio, latitud y longitud. Si la sucursal no tiene coordenadas, SHALL incluir el código postal y dejar las coordenadas vacías; si no hay sucursal, SHALL usar la ubicación de la biblioteca. SHALL NOT inventar coordenadas.

#### Scenario: Sucursal con coordenadas

- **WHEN** un ejemplar pertenece a una sucursal con latitud y longitud
- **THEN** su `ubicacion` incluye el código postal, el municipio y las coordenadas de la sucursal

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** un ejemplar pertenece a una sucursal con código postal pero sin coordenadas
- **THEN** su `ubicacion` incluye el código postal y el municipio
- **AND** la latitud y la longitud quedan vacías

#### Scenario: Ejemplar sin sucursal

- **WHEN** un ejemplar no tiene una sucursal resoluble y su biblioteca tiene datos de ubicación
- **THEN** su `ubicacion` usa el código postal y las coordenadas de la biblioteca

#### Scenario: Ejemplar sin ubicación

- **WHEN** un ejemplar no tiene sucursal ni biblioteca con datos de ubicación
- **THEN** su `ubicacion` queda vacía
- **AND** no se inventan coordenadas ni código postal

#### Scenario: Compatibilidad del contrato

- **WHEN** un cliente anterior consume la ficha de registro
- **THEN** sigue recibiendo los campos existentes
- **AND** el nuevo campo de ubicación es opcional
