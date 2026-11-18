# Spec Delta

## MODIFIED Requirements

### Requirement: Documento de índice

El indexador MUST construir un documento por edición con `record_id`, fuente, título, título uniforme, sinopsis, personas y roles, géneros, materias, soportes, año, idioma, país, duración, edad recomendada, EAN, bibliotecas tenedoras, ubicaciones filtrables y número de ejemplares. El documento SHALL NOT incluir ningún campo de disponibilidad de préstamo.

#### Scenario: Edición indexada

- **WHEN** se indexa una edición con ejemplares en DVD
- **THEN** el documento contiene `soportes: ["DVD"]`, su `record_id` y su `fuente`
- **AND** contiene las bibliotecas tenedoras, las ubicaciones filtrables y el número de ejemplares
- **AND** no contiene ningún campo de disponibilidad

#### Scenario: Mismo TITN en dos fuentes

- **WHEN** se indexan dos ediciones con el mismo `TITN` en fuentes distintas
- **THEN** existen dos documentos con `id` distintos
- **AND** cada documento conserva su `fuente` y sus propias ubicaciones

### Requirement: Ubicaciones filtrables en el índice

El documento SHALL conservar los nombres de las redes en `bibliotecas` y SHALL incluir `ubicaciones` con códigos estables que incluyan la fuente (`b:<fuente>:<biblioteca>` para biblioteca, `s:<fuente>:<sucursal>` para sucursal) y `ubicaciones_texto` con los nombres visibles. La fuente SHALL ser un campo filtrable independiente.

#### Scenario: Edición con sucursal

- **WHEN** se indexa una edición con un ejemplar en una sucursal
- **THEN** `ubicaciones` contiene el código de la red y el de la sucursal, ambos con la fuente
- **AND** `ubicaciones_texto` contiene ambos nombres visibles
- **AND** `bibliotecas` sigue conteniendo solo el nombre de la red

#### Scenario: Misma red en dos fuentes

- **WHEN** dos fuentes tienen una biblioteca con el mismo código o el mismo nombre
- **THEN** sus códigos en `ubicaciones` incluyen la fuente
- **AND** un filtro por una de ellas no devuelve la otra sin el filtro de fuente

### Requirement: Facetas

La búsqueda MUST devolver distribuciones de facetas para `soporte`, `genero`, `anio`, `idioma`, `paises_origen`, `biblioteca` y `fuente`. La faceta de disponibilidad SHALL NOT existir.

#### Scenario: Faceta de soporte

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados para DVD y Blu-ray
- **AND** no incluye una faceta de disponibilidad

#### Scenario: Faceta de país de origen

- **WHEN** el usuario busca `cine` sin filtros
- **THEN** la respuesta incluye el número de resultados por cada código de `paises_origen`
- **AND** las ediciones sin países de TMDB no se asignan a ningún país

#### Scenario: Faceta de fuente

- **WHEN** el usuario busca sin filtros y hay ediciones de varias fuentes
- **THEN** la respuesta incluye el número de resultados por fuente
- **AND** las fuentes sin resultados no aparecen o aparecen con cero de forma consistente

### Requirement: Filtros combinados

El sistema SHALL combinar filtros de soporte, género, rango de años, idioma, país de origen, biblioteca y fuente con la consulta textual. El filtro de disponibilidad SHALL NOT aceptarse.

#### Scenario: DVD disponibles en una biblioteca

- **WHEN** el usuario filtra por `soporte=DVD` y `biblioteca=s:madrid:BMALC1`
- **THEN** solo se devuelven ediciones con al menos un ejemplar DVD en esa sucursal
- **AND** no se ofrece ningún filtro por disponibilidad

#### Scenario: Filtro por nombre de biblioteca o sucursal

- **WHEN** el usuario filtra por `biblioteca=B.P.M. Cardenal Cisneros`
- **THEN** se buscan coincidencias en `bibliotecas` y en `ubicaciones_texto`
- **AND** el filtro se combina con la consulta textual y el resto de filtros activos

#### Scenario: Filtro por fuente

- **WHEN** el usuario filtra por `fuente=madrid`
- **THEN** solo se devuelven ediciones de esa fuente
- **AND** el filtro se combina con la consulta textual y el resto de filtros activos

#### Scenario: Código de ubicación histórico

- **WHEN** el usuario filtra por un código antiguo sin fuente, como `b:RBMALC`
- **THEN** se resuelve como `b:madrid:RBMALC`
- **AND** el resultado es equivalente al del código nuevo

#### Scenario: Filtro por país de origen

- **WHEN** el usuario filtra por `paises_origen=ES`
- **THEN** solo se devuelven ediciones cuya lista `paises_origen` contiene `ES`
- **AND** el filtro se combina con la consulta textual y el resto de filtros activos

#### Scenario: Varios países seleccionados

- **WHEN** el usuario filtra por `paises_origen=ES` y `paises_origen=FR`
- **THEN** se devuelven las ediciones que contienen `ES` o `FR`
- **AND** la respuesta mantiene el resto de filtros aplicados
