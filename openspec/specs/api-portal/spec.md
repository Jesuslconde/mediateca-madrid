# api-portal Specification

## Purpose
Exponer los datos normalizados y el índice de búsqueda mediante una API HTTP estable para que el portal web y otros clientes puedan consultar el catálogo.

## Requirements

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

### Requirement: Bibliotecas y estadísticas

La API SHALL exponer la lista de bibliotecas con su número de ejemplares y estadísticas agregadas por soporte, sin contadores de disponibilidad de préstamo.

#### Scenario: Listado de bibliotecas

- **WHEN** el cliente solicita `/api/libraries`
- **THEN** recibe las bibliotecas conocidas con su municipio y número de ejemplares
- **AND** no recibe contadores de ejemplares disponibles

### Requirement: Ubicaciones filtrables

La API SHALL exponer `GET /api/locations` con las redes y sucursales que tienen ejemplares. Cada ubicación SHALL incluir un código estable con prefijo (`b:` para biblioteca, `s:` para sucursal), nombre visible, tipo, biblioteca matriz, municipio y número de ejemplares.

#### Scenario: Listado de ubicaciones

- **WHEN** el cliente solicita `/api/locations`
- **THEN** recibe una entrada `b:<biblioteca_codigo>` por cada red
- **AND** recibe una entrada `s:<sucursal_codigo>` por cada sucursal con ejemplares
- **AND** cada sucursal incluye el código y nombre de su biblioteca matriz

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

### Requirement: Ubicación de ejemplares en la ficha

La respuesta de `GET /api/records/{titn}` SHALL incluir por ejemplar una `ubicacion` opcional con código postal, municipio, latitud y longitud. Si la sucursal no tiene coordenadas, SHALL incluir el código postal y dejar las coordenadas vacías; si no hay sucursal, SHALL usar la ubicación de la biblioteca. SHALL NOT inventar coordenadas.

#### Scenario: Sucursal con coordenadas

- **WHEN** un ejemplar pertenece a una sucursal con latitud y longitud
- **THEN** su `ubicacion` incluye el código postal, el municipio y las coordenadas de la sucursal

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** un ejemplar pertenece a una sucursal con código postal pero sin coordenadas
- **THEN** su `ubicacion` incluye el código postal y el municipio
- **AND** la latitud y la longitud quedan vacías

#### Scenario: Ejemplar sin sucursal

- **WHEN** un ejemplar no tiene una sucursal resoluble y su biblioteca tiene datos de ubicación
- **THEN** su `ubicacion` usa el código postal y las coordenadas de la biblioteca

#### Scenario: Ejemplar sin ubicación

- **WHEN** un ejemplar no tiene sucursal ni biblioteca con datos de ubicación
- **THEN** su `ubicacion` queda vacía
- **AND** no se inventan coordenadas ni código postal

#### Scenario: Compatibilidad del contrato

- **WHEN** un cliente anterior consume la ficha de registro
- **THEN** sigue recibiendo los campos existentes
- **AND** el nuevo campo de ubicación es opcional

### Requirement: Recursos de lista

La API SHALL exponer `POST /api/lists`, `GET /api/lists/{token}`, `POST /api/lists/{token}/items`, `DELETE /api/lists/{token}/items/{titn}` y `PATCH /api/lists/{token}`. El token SHALL actuar como credencial de lectura y edicion y SHALL almacenarse hasheado. Las mutaciones de elementos SHALL devolver el numero actualizado de elementos.

#### Scenario: Crear una lista

- **WHEN** el cliente envia `POST /api/lists`
- **THEN** la API crea una lista vacia
- **AND** devuelve el token una sola vez
- **AND** en la base de datos solo queda el hash del token

#### Scenario: Consultar una lista

- **WHEN** el cliente solicita `GET /api/lists/{token}` con un token valido
- **THEN** recibe el titulo, las fechas, el numero de elementos y los elementos de la lista

#### Scenario: Anadir y quitar elementos

- **WHEN** el cliente envia `POST /api/lists/{token}/items` con un `titn`
- **THEN** la edicion se anade si no estaba
- **AND** una segunda peticion con el mismo `titn` no duplica la entrada
- **AND** `DELETE /api/lists/{token}/items/{titn}` la elimina
- **AND** la respuesta incluye el numero actualizado de elementos

#### Scenario: Anadir una edicion inexistente

- **WHEN** el cliente envia un `titn` que no existe en el catalogo
- **THEN** la API responde con 422
- **AND** la lista no cambia

#### Scenario: Token invalido

- **WHEN** el cliente usa un token desconocido o caducado
- **THEN** la API responde con 404
- **AND** no revela si la lista existio

### Requirement: Escritura acotada al catalogo

La API SHALL escribir unicamente en las tablas de listas. SHALL NOT modificar tablas del catalogo y el resto de recursos SHALL seguir siendo de solo lectura.

#### Scenario: Una mutacion de lista no altera el catalogo

- **WHEN** se crea una lista o se anade o quita un elemento
- **THEN** ninguna tabla del catalogo cambia

#### Scenario: Recursos de catalogo de solo lectura

- **WHEN** un cliente intenta una operacion de escritura sobre un recurso del catalogo
- **THEN** la API no la admite
- **AND** los endpoints de busqueda, ficha, bibliotecas y estadisticas siguen exponiendose como lectura

### Requirement: Forma de la respuesta de lista

La respuesta de una lista SHALL incluir su titulo, fechas, numero de elementos y cada elemento con `titn`, titulo vigente o guardado, soportes, ano, portada y URL del OPAC cuando existan. Los elementos SHALL devolverse del mas reciente al mas antiguo.

#### Scenario: Lista con elementos disponibles

- **WHEN** el cliente consulta una lista con ediciones presentes en el catalogo
- **THEN** cada elemento incluye los datos vigentes de la edicion
- **AND** incluye la URL de su ficha en el OPAC

#### Scenario: Orden de los elementos

- **WHEN** el cliente consulta una lista con varios elementos
- **THEN** los recibe ordenados del mas reciente al mas antiguo

#### Scenario: Elemento sin ficha vigente

- **WHEN** una edicion guardada ya no existe en el catalogo
- **THEN** el elemento incluye el titulo guardado
- **AND** indica que la ficha no esta disponible
- **AND** la lista sigue respondiendo con el resto de elementos

### Requirement: Errores y limites de lista

La API SHALL devolver 404 para tokens desconocidos o caducados, 409 al anadir a una lista llena, 422 para una edicion inexistente y 429 al superar el limite de creacion. Los errores MUST ser JSON consistentes con el resto de la API.

#### Scenario: Lista llena

- **WHEN** se intenta anadir una edicion a una lista que ya tiene 200
- **THEN** la API responde con 409
- **AND** devuelve un mensaje legible
- **AND** no modifica la lista

#### Scenario: Limite de creacion superado

- **WHEN** un mismo origen supera el numero de listas permitidas en la ventana
- **THEN** la API responde con 429
- **AND** no crea la lista
