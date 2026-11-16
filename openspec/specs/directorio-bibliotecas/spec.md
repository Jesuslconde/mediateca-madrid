# directorio-bibliotecas Specification

## Purpose

Mantener actualizada la ubicación de las sucursales bibliotecarias a partir del Directorio de Bibliotecas de la Comunidad de Madrid, para que el catálogo disponga de dirección, código postal y coordenadas fiables sin depender de geocodificación en tiempo de consulta.

## Requirements

### Requirement: Fichas de sucursal del directorio

El sistema SHALL recorrer la paginación del Directorio de Bibliotecas de la Comunidad de Madrid y SHALL leer cada ficha de sucursal para extraer nombre, código `SUBC`, biblioteca, sucursal, dirección, municipio, código postal y coordenadas del enlace de mapa cuando existan. SHALL NOT persistir HTML crudo.

#### Scenario: Ficha con coordenadas

- **WHEN** una ficha del directorio declara un `SUBC` y un enlace de mapa con coordenada `ll=`
- **THEN** se guardan los códigos de biblioteca y sucursal, la dirección, el código postal y las coordenadas
- **AND** no se guarda el HTML de la ficha

#### Scenario: Ficha sin coordenadas

- **WHEN** una ficha declara dirección y código postal pero su enlace de mapa solo contiene una consulta de dirección
- **THEN** se guardan los códigos, la dirección y el código postal
- **AND** la latitud y la longitud quedan vacías

#### Scenario: Ficha sin SUBC

- **WHEN** una ficha del directorio no declara ningún `SUBC`
- **THEN** la ficha se omite
- **AND** la omisión se contabiliza en el resumen de la actualización

#### Scenario: Biblioteca cerrada

- **WHEN** el nombre de la ficha indica que la biblioteca está cerrada
- **THEN** la ficha se omite
- **AND** no se crea ni se actualiza ninguna sucursal

#### Scenario: Biblioteca móvil

- **WHEN** la ficha corresponde a una biblioteca móvil o bibliobús
- **THEN** no se usan las coordenadas de sus paradas como ubicación de sucursal
- **AND** se conservan el municipio y el código postal cuando estén disponibles

### Requirement: Emparejamiento por código

El sistema SHALL emparejar el `SUBC` del directorio con los códigos de biblioteca y sucursal del OPAC, SHALL actualizar la sucursal existente sin duplicarla y SHALL omitir los códigos que no correspondan a una biblioteca conocida del catálogo.

#### Scenario: Sucursal conocida

- **WHEN** una ficha del directorio tiene `SUBC=RBMALC/BMALC1` y el catálogo ya tiene esa biblioteca y sucursal
- **THEN** se actualizan el nombre, la dirección, el código postal y las coordenadas de la sucursal existente
- **AND** no se crea una sucursal duplicada

#### Scenario: Reproceso idempotente

- **WHEN** se vuelve a ejecutar la actualización sobre las mismas fichas
- **THEN** las sucursales se actualizan en su sitio
- **AND** el número de sucursales no aumenta

#### Scenario: Biblioteca desconocida

- **WHEN** una ficha del directorio declara una biblioteca que no existe en el catálogo
- **THEN** la ficha se omite
- **AND** la omisión se contabiliza en el resumen de la actualización

#### Scenario: Ficha de ámbito de biblioteca

- **WHEN** una ficha del directorio declara solo el código de biblioteca, sin código de sucursal
- **THEN** se actualizan los datos de ubicación de la biblioteca
- **AND** no se crea una sucursal adicional

### Requirement: Coordenadas fiables

El sistema SHALL usar únicamente la coordenada `ll=` del enlace de mapa y SHALL ignorar `sll=`, `sspn=` y el centro de mapa por defecto. Si no hay coordenada fiable, SHALL dejar latitud y longitud vacías y conservar el código postal cuando exista.

#### Scenario: Centro de mapa obsoleto

- **WHEN** el enlace de mapa contiene un `sll=` que no corresponde a la dirección y un `ll=` que sí corresponde
- **THEN** se usa el valor de `ll=`
- **AND** se ignora el valor de `sll=`

#### Scenario: Solo consulta de dirección

- **WHEN** el enlace de mapa solo contiene una consulta `q=` con la dirección
- **THEN** no se extraen coordenadas
- **AND** se conserva el código postal de la ficha

#### Scenario: Enlace corto de mapa

- **WHEN** el enlace de mapa es un enlace corto que no contiene coordenadas
- **THEN** no se extraen coordenadas
- **AND** la ficha sigue siendo válida para el resto de campos

#### Scenario: Mapa por defecto del OPAC

- **WHEN** la única coordenada disponible es la vista por defecto del OPAC
- **THEN** esa coordenada no se usa como ubicación de la sucursal

### Requirement: Actualización manual y cobertura

El sistema SHALL ofrecer un comando de actualización manual e idempotente del directorio, con retardo configurable y límite opcional, que SHALL informar de fichas leídas, con `SUBC`, con código postal, con coordenadas, emparejadas y omitidas. SHALL NOT borrar sucursales ausentes ni geocodificar direcciones en esta versión.

#### Scenario: Resumen de cobertura

- **WHEN** termina una actualización del directorio
- **THEN** el comando muestra el número de fichas leídas, con `SUBC`, con código postal, con coordenadas, emparejadas y omitidas

#### Scenario: Sucursal ausente

- **WHEN** una sucursal existente no aparece en una actualización posterior
- **THEN** la sucursal se conserva
- **AND** no se elimina automáticamente

#### Scenario: Coordenadas existentes

- **WHEN** una ficha actualizada no aporta coordenadas y la sucursal ya tenía coordenadas guardadas
- **THEN** se conservan las coordenadas existentes
- **AND** no se sobrescriben con valores vacíos

#### Scenario: Sin geocodificación

- **WHEN** una ficha no aporta coordenadas
- **THEN** el comando no invoca ningún servicio externo de geocodificación
- **AND** la resolución de la distancia queda en manos del portal mediante el código postal
