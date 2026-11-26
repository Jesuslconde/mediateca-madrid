# Spec Delta

## ADDED Requirements

### Requirement: Filtro por proximidad

La búsqueda SHALL poder acotarse a las ediciones con al menos un ejemplar en una sucursal situada dentro de un radio respecto a un código postal de referencia. El filtro SHALL combinarse con la consulta textual y el resto de filtros activos.

#### Scenario: Edición en una sucursal cercana

- **WHEN** el usuario filtra por un código postal y un radio
- **THEN** solo se devuelven ediciones con al menos un ejemplar en una sucursal dentro del radio
- **AND** las ediciones sin ejemplares dentro del radio no aparecen

#### Scenario: Combinación con otros filtros

- **WHEN** el usuario combina el radio con un soporte o un género
- **THEN** el filtro de proximidad se aplica junto con el resto
- **AND** los totales y las facetas se calculan sobre el conjunto acotado

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** una sucursal solo tiene código postal cuyo centroide queda dentro del radio
- **THEN** sus ejemplares cuentan como dentro del radio
- **AND** la edición se devuelve si tiene al menos un ejemplar en ella

#### Scenario: Sin código postal ni radio

- **WHEN** no se indica código postal ni radio
- **THEN** la búsqueda no se acota por distancia
- **AND** se comporta como la búsqueda sin filtro de proximidad

### Requirement: Exclusión de ubicaciones del conjunto cercano

La búsqueda SHALL permitir excluir ubicaciones del conjunto cercano. Una edición SHALL ocultarse solo cuando no tenga ejemplares fuera de las ubicaciones excluidas; si conserva al menos un ejemplar en una ubicación no excluida, SHALL seguir apareciendo.

#### Scenario: Excluir una sucursal

- **WHEN** el usuario excluye una sucursal del conjunto cercano
- **THEN** las ediciones que solo tienen ejemplares en esa sucursal no aparecen
- **AND** las ediciones con ejemplares en otras sucursales no excluidas siguen apareciendo

#### Scenario: Excluir una red

- **WHEN** el usuario excluye una biblioteca (red) del conjunto cercano
- **THEN** se excluyen todas sus sucursales
- **AND** las ediciones que solo tienen ejemplares en esa red no aparecen
