# api-portal Specification

## Purpose
Exponer los datos normalizados y el índice de búsqueda mediante una API HTTP estable para que el portal web y otros clientes puedan consultar el catálogo.

## Requirements

### Requirement: Búsqueda paginada

La API MUST exponer `GET /api/search` con parámetros de consulta, filtros, orden, página y límite, y SHALL devolver resultados, total y facetas.

#### Scenario: Búsqueda con filtros

- **WHEN** el cliente solicita `/api/search?q=cine&soporte=Blu-ray&page=1&limit=20`
- **THEN** recibe hasta 20 resultados de Blu-ray
- **AND** recibe el total y las distribuciones de facetas

### Requirement: Ficha de registro

La API MUST exponer `GET /api/records/{titn}` y SHALL devolver metadatos de la edición, obra asociada, personas con rol, materias, enlaces, la URL original del OPAC y los ejemplares agrupables por biblioteca. La respuesta SHALL NOT incluir campos de disponibilidad de préstamo.

#### Scenario: Ficha existente

- **WHEN** el cliente solicita un `TITN` existente
- **THEN** recibe la ficha completa con sus ejemplares
- **AND** cada ejemplar indica biblioteca, sucursal, signatura, tipo y soporte
- **AND** la ficha incluye `source_url` con la ficha original del OPAC

#### Scenario: Ficha inexistente

- **WHEN** el cliente solicita un `TITN` que no existe
- **THEN** la API responde con código 404
- **AND** devuelve un mensaje de error legible

### Requirement: Bibliotecas y estadísticas

La API SHALL exponer la lista de bibliotecas con su número de ejemplares y estadísticas agregadas por soporte, sin contadores de disponibilidad de préstamo.

#### Scenario: Listado de bibliotecas

- **WHEN** el cliente solicita `/api/libraries`
- **THEN** recibe las bibliotecas conocidas con su municipio y número de ejemplares
- **AND** no recibe contadores de ejemplares disponibles

### Requirement: Salud del servicio

La API MUST exponer `GET /health` y SHALL comprobar la conexión con PostgreSQL y Meilisearch.

#### Scenario: Servicios disponibles

- **WHEN** PostgreSQL y Meilisearch responden correctamente
- **THEN** `/health` devuelve estado `ok`

### Requirement: CORS y errores

La API SHALL permitir CORS para el frontend configurado y MUST devolver errores JSON consistentes.

#### Scenario: Error de validación

- **WHEN** un parámetro tiene un tipo inválido
- **THEN** la API responde con código 422
- **AND** el cuerpo JSON identifica el campo y el motivo

### Requirement: Enlace a la ficha del OPAC

Cada registro SHALL exponer la URL de su ficha original en el OPAC para que el cliente pueda consultar allí el estado de préstamo actual.

#### Scenario: Registro con URL de origen

- **WHEN** el cliente consulta un registro recolectado del OPAC
- **THEN** la respuesta incluye `source_url`
- **AND** la URL apunta a la ficha original del registro
