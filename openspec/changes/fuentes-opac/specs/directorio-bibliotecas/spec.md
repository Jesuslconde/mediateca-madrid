# Spec Delta

## MODIFIED Requirements

### Requirement: Emparejamiento por código

El sistema SHALL emparejar el `SUBC` del directorio con los códigos de biblioteca y sucursal del OPAC de la misma fuente, SHALL actualizar la sucursal existente sin duplicarla y SHALL omitir los códigos que no correspondan a una biblioteca conocida de esa fuente.

#### Scenario: Sucursal conocida

- **WHEN** una ficha del directorio de Madrid tiene `SUBC=RBMALC/BMALC1` y el catálogo ya tiene esa biblioteca y sucursal en Madrid
- **THEN** se actualizan el nombre, la dirección, el código postal y las coordenadas de la sucursal existente
- **AND** no se crea una sucursal duplicada

#### Scenario: Reproceso idempotente

- **WHEN** se vuelve a ejecutar la actualización sobre las mismas fichas
- **THEN** las sucursales se actualizan en su sitio
- **AND** el número de sucursales no aumenta

#### Scenario: Biblioteca desconocida

- **WHEN** una ficha del directorio declara una biblioteca que no existe en el catálogo de esa fuente
- **THEN** la ficha se omite
- **AND** la omisión se contabiliza en el resumen de la actualización

#### Scenario: Ficha de ámbito de biblioteca

- **WHEN** una ficha del directorio declara solo el código de biblioteca, sin código de sucursal
- **THEN** se actualizan los datos de ubicación de la biblioteca
- **AND** no se crea una sucursal adicional

#### Scenario: Código de otra fuente

- **WHEN** una ficha del directorio de Madrid declara un código que solo existe en otra fuente
- **THEN** la ficha se omite para Madrid
- **AND** no se actualiza ninguna biblioteca de la otra fuente

## ADDED Requirements

### Requirement: Directorio por fuente

Cada fuente SHALL poder declarar su propio directorio de bibliotecas y su propio procedimiento de extracción. La actualización de un directorio SHALL limitarse a la fuente que lo declara y SHALL NOT modificar bibliotecas o sucursales de otras fuentes.

#### Scenario: Directorio de Madrid

- **WHEN** se ejecuta la actualización del directorio de Madrid
- **THEN** solo se procesan las fichas de esa fuente
- **AND** las bibliotecas y sucursales de otras fuentes permanecen intactas

#### Scenario: Fuente sin directorio

- **WHEN** una fuente no tiene directorio configurado
- **THEN** la actualización de esa fuente no se ejecuta
- **AND** el sistema informa de que no hay directorio disponible sin fallar el resto de fuentes
