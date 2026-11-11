# busqueda-facetas Specification

## Purpose
Ofrecer una búsqueda rápida y tolerante a errores sobre el catálogo de vídeos, con facetas que permitan acotar por soporte, género, año, idioma, biblioteca y disponibilidad.

## Requirements

### Requirement: Documento de índice

El indexador MUST construir un documento por edición con título, título uniforme, sinopsis, personas y roles, géneros, materias, soportes, año, idioma, país, duración, edad recomendada, EAN, bibliotecas tenedoras y número de ejemplares. El documento SHALL NOT incluir ningún campo de disponibilidad de préstamo.

#### Scenario: Edición indexada

- **WHEN** se indexa una edición con ejemplares en DVD
- **THEN** el documento contiene `soportes: ["DVD"]`
- **AND** contiene las bibliotecas tenedoras y el número de ejemplares
- **AND** no contiene ningún campo de disponibilidad

### Requirement: Búsqueda textual

La búsqueda SHALL usar los campos textuales principales y MUST devolver resultados paginados con puntuación de relevancia.

#### Scenario: Búsqueda por título

- **WHEN** el usuario busca `abejas`
- **THEN** aparecen los registros cuyo título o sinopsis contiene el término
- **AND** los resultados indican el total y la página actual

### Requirement: Facetas

La búsqueda MUST devolver distribuciones de facetas para `soporte`, `genero`, `anio`, `idioma`, `paises_origen` y `biblioteca`. La faceta de disponibilidad SHALL NOT existir.

#### Scenario: Faceta de soporte

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados para DVD y Blu-ray
- **AND** no incluye una faceta de disponibilidad

#### Scenario: Faceta de país de origen

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados por cada código de `paises_origen`
- **AND** las ediciones sin países de TMDB no se asignan a ningún país

### Requirement: Filtros combinados

El sistema SHALL combinar filtros de soporte, género, rango de años, idioma, país de origen y biblioteca con la consulta textual. El filtro de disponibilidad SHALL NOT aceptarse.

#### Scenario: DVD disponibles en una biblioteca

- **WHEN** el usuario filtra por `soporte=DVD` y `biblioteca=B.P.M. Cardenal Cisneros`
- **THEN** solo se devuelven ediciones con al menos un ejemplar DVD en esa biblioteca
- **AND** no se ofrece ningún filtro por disponibilidad

#### Scenario: Filtro por país de origen

- **WHEN** el usuario filtra por `paises_origen=ES`
- **THEN** solo se devuelven ediciones cuya lista `paises_origen` contiene `ES`
- **AND** el filtro se combina con la consulta textual y el resto de filtros activos

#### Scenario: Varios países seleccionados

- **WHEN** el usuario filtra por `paises_origen=ES` y `paises_origen=FR`
- **THEN** se devuelven las ediciones que contienen `ES` o `FR`
- **AND** la respuesta mantiene el resto de filtros aplicados

### Requirement: Ordenación

Los resultados SHALL poder ordenarse por relevancia, año de publicación, título o duración.

#### Scenario: Orden por año descendente

- **WHEN** el usuario selecciona ordenar por año descendente
- **THEN** los resultados se muestran del más reciente al más antiguo
