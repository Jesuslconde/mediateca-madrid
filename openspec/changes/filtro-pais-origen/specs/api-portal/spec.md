# Spec Delta

## ADDED Requirements

### Requirement: Países de origen en los resultados

Cada resultado de `GET /api/search` MUST incluir `paises_origen` como lista de códigos ISO 3166-1 alfa-2 en mayúsculas, vacía cuando la edición no tenga países conocidos.

#### Scenario: Resultado con países

- **WHEN** el cliente consulta `/api/search?q=cine`
- **THEN** cada resultado incluye `paises_origen`
- **AND** una edición enriquecida con España y Francia devuelve `["ES", "FR"]`

#### Scenario: Resultado sin países

- **WHEN** una edición no tiene países de TMDB
- **THEN** el resultado incluye `paises_origen: []`
- **AND** el resultado sigue apareciendo en la búsqueda

## MODIFIED Requirements

### Requirement: Búsqueda paginada

La API MUST exponer `GET /api/search` con parámetros de consulta, filtros, orden, página y límite, y SHALL devolver resultados, total y facetas. Entre los filtros SHALL aceptar `paises_origen`, repetible para seleccionar varios países.

#### Scenario: Búsqueda con filtros

- **WHEN** el cliente solicita `/api/search?q=cine&soporte=Blu-ray&page=1&limit=20`
- **THEN** recibe hasta 20 resultados de Blu-ray
- **AND** recibe el total y las distribuciones de facetas

#### Scenario: Filtro por país de origen

- **WHEN** el cliente solicita `/api/search?q=cine&paises_origen=ES&paises_origen=FR`
- **THEN** recibe las ediciones que contienen `ES` o `FR`
- **AND** el resto de filtros y la consulta textual se aplican conjuntamente

### Requirement: Ficha de registro

La API MUST exponer `GET /api/records/{titn}` y SHALL devolver metadatos de la edición, obra asociada, personas con rol, materias, enlaces, la URL original del OPAC, los países de origen y los ejemplares agrupables por biblioteca. La respuesta SHALL NOT incluir campos de disponibilidad de préstamo.

#### Scenario: Ficha existente

- **WHEN** el cliente solicita un `TITN` existente
- **THEN** recibe la ficha completa con sus ejemplares
- **AND** cada ejemplar indica biblioteca, sucursal, signatura, tipo y soporte
- **AND** la ficha incluye `source_url` con la ficha original del OPAC
- **AND** la ficha incluye `paises_origen` como lista de códigos ISO

#### Scenario: Ficha inexistente

- **WHEN** el cliente solicita un `TITN` que no existe
- **THEN** la API responde con código 404
- **AND** devuelve un mensaje de error legible
