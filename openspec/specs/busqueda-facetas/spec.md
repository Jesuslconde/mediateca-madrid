# busqueda-facetas Specification

## Purpose
Ofrecer una búsqueda rápida y tolerante a errores sobre el catálogo de vídeos, con facetas que permitan acotar por soporte, género, año, idioma, biblioteca y disponibilidad.

## Requirements

### Requirement: Documento de índice

El indexador MUST construir un documento por edición con título, título uniforme, sinopsis, personas y roles, géneros, materias, soportes, año, idioma, país, duración, edad recomendada, EAN, bibliotecas, disponibilidad y número de ejemplares.

#### Scenario: Edición indexada

- **WHEN** se indexa una edición con ejemplares en DVD
- **THEN** el documento contiene `soportes: ["DVD"]`
- **AND** contiene las bibliotecas y el estado de disponibilidad agregado

### Requirement: Búsqueda textual

La búsqueda SHALL usar los campos textuales principales y MUST devolver resultados paginados con puntuación de relevancia.

#### Scenario: Búsqueda por título

- **WHEN** el usuario busca `abejas`
- **THEN** aparecen los registros cuyo título o sinopsis contiene el término
- **AND** los resultados indican el total y la página actual

### Requirement: Facetas

La búsqueda MUST devolver distribuciones de facetas para `soporte`, `genero`, `anio`, `idioma`, `biblioteca` y `disponible`.

#### Scenario: Faceta de soporte

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados para DVD y Blu-ray

### Requirement: Filtros combinados

El sistema SHALL combinar filtros de soporte, género, rango de años, idioma, biblioteca y disponibilidad con la consulta textual.

#### Scenario: DVD disponibles en una biblioteca

- **WHEN** el usuario filtra por `soporte=DVD`, `biblioteca=B.P.M. Cardenal Cisneros` y `disponible=true`
- **THEN** solo se devuelven ediciones con al menos un ejemplar DVD disponible en esa biblioteca

### Requirement: Ordenación

Los resultados SHALL poder ordenarse por relevancia, año de publicación, título o duración.

#### Scenario: Orden por año descendente

- **WHEN** el usuario selecciona ordenar por año descendente
- **THEN** los resultados se muestran del más reciente al más antiguo
