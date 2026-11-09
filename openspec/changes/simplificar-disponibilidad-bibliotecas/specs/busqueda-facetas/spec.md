# busqueda-facetas Spec Delta

## MODIFIED Requirements

### Requirement: Documento de índice

El indexador MUST construir un documento por edición con título, título uniforme, sinopsis, personas y roles, géneros, materias, soportes, año, idioma, país, duración, edad recomendada, EAN, bibliotecas tenedoras y número de ejemplares. El documento SHALL NOT incluir ningún campo de disponibilidad de préstamo.

#### Scenario: Edición indexada

- **WHEN** se indexa una edición con ejemplares en DVD
- **THEN** el documento contiene `soportes: ["DVD"]`
- **AND** contiene las bibliotecas tenedoras y el número de ejemplares
- **AND** no contiene ningún campo de disponibilidad

### Requirement: Facetas

La búsqueda MUST devolver distribuciones de facetas para `soporte`, `genero`, `anio`, `idioma` y `biblioteca`. La faceta de disponibilidad SHALL NOT existir.

#### Scenario: Faceta de soporte

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados para DVD y Blu-ray
- **AND** no incluye una faceta de disponibilidad

### Requirement: Filtros combinados

El sistema SHALL combinar filtros de soporte, género, rango de años, idioma y biblioteca con la consulta textual. El filtro de disponibilidad SHALL NOT aceptarse.

#### Scenario: DVD disponibles en una biblioteca

- **WHEN** el usuario filtra por `soporte=DVD` y `biblioteca=B.P.M. Cardenal Cisneros`
- **THEN** solo se devuelven ediciones con al menos un ejemplar DVD en esa biblioteca
- **AND** no se ofrece ningún filtro por disponibilidad
