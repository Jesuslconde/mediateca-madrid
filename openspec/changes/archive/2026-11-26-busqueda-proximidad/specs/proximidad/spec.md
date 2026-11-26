# Spec Delta

## Purpose

Resolver la cercanía entre un código postal de referencia y las sucursales del catálogo para poder acotar la búsqueda por distancia.

## ADDED Requirements

### Requirement: Centroide del código postal de referencia

El sistema SHALL resolver un código postal de cinco dígitos a su centroide (latitud y longitud) usando los centroides de códigos postales disponibles. Un código postal desconocido SHALL dejar la referencia sin resolver, sin provocar error.

#### Scenario: Código postal conocido

- **WHEN** se resuelve un código postal presente en la tabla de centroides
- **THEN** se obtienen su latitud y su longitud
- **AND** su municipio asociado cuando esté disponible

#### Scenario: Código postal desconocido

- **WHEN** se resuelve un código postal que no está en la tabla
- **THEN** la referencia queda sin centroide
- **AND** no se lanza ningún error

### Requirement: Distancia en línea recta

El sistema SHALL calcular la distancia en kilómetros entre dos puntos como distancia en línea recta aproximada.

#### Scenario: Distancia entre dos puntos

- **WHEN** se calcula la distancia entre dos coordenadas conocidas
- **THEN** el resultado es la distancia aproximada en kilómetros
- **AND** no representa una ruta ni un itinerario

### Requirement: Sucursales dentro de un radio

Dado un centroide de referencia y un radio, el sistema SHALL determinar qué sucursales quedan dentro. La ubicación de una sucursal SHALL ser sus coordenadas y, si no las tiene, el centroide de su código postal.

#### Scenario: Sucursal con coordenadas

- **WHEN** una sucursal tiene coordenadas dentro del radio
- **THEN** la sucursal se incluye en el conjunto cercano

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** una sucursal no tiene coordenadas pero el centroide de su código postal queda dentro del radio
- **THEN** la sucursal se incluye usando ese centroide

#### Scenario: Sucursal fuera del radio

- **WHEN** una sucursal queda fuera del radio
- **THEN** la sucursal se excluye del conjunto cercano

#### Scenario: Biblioteca sin sucursales

- **WHEN** una biblioteca no tiene sucursales y su propio punto queda dentro del radio
- **THEN** la biblioteca se incluye en el conjunto cercano

### Requirement: Degradación sin ubicación

Una sucursal sin coordenadas y sin código postal utilizable SHALL quedar fuera del conjunto cercano, sin interrumpir la resolución del resto.

#### Scenario: Sucursal sin ubicación

- **WHEN** una sucursal no tiene coordenadas ni código postal con centroide
- **THEN** la sucursal queda fuera del conjunto cercano
- **AND** el resto de sucursales se resuelve con normalidad
