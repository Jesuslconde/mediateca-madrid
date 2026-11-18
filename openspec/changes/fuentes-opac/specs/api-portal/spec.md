# Spec Delta

## MODIFIED Requirements

### Requirement: Búsqueda paginada

La API MUST exponer `GET /api/search` con parámetros de consulta, filtros, orden, página y límite, y SHALL devolver resultados, total y facetas. Entre los filtros SHALL aceptar `paises_origen`, repetible para seleccionar varios países, y `fuente`.

#### Scenario: Búsqueda con filtros

- **WHEN** el cliente solicita `/api/search?q=cine&soporte=Blu-ray&page=1&limit=20`
- **THEN** recibe hasta 20 resultados de Blu-ray
- **AND** recibe el total y las distribuciones de facetas

#### Scenario: Filtro por país de origen

- **WHEN** el cliente solicita `/api/search?q=cine&paises_origen=ES&paises_origen=FR`
- **THEN** recibe las ediciones que contienen `ES` o `FR`
- **AND** el resto de filtros y la consulta textual se aplican conjuntamente

#### Scenario: Filtro por fuente

- **WHEN** el cliente solicita `/api/search?q=cine&fuente=madrid`
- **THEN** recibe solo ediciones de la fuente indicada
- **AND** cada resultado incluye su `fuente` y su `record_id`

### Requirement: Ficha de registro

La API MUST exponer `GET /api/records/{record_id}` y SHALL devolver metadatos de la edición, su fuente, la obra asociada, personas con rol, materias, enlaces, la URL original del OPAC, los países de origen y los ejemplares agrupables por biblioteca. La respuesta SHALL NOT incluir campos de disponibilidad de préstamo.

#### Scenario: Ficha existente

- **WHEN** el cliente solicita un `record_id` existente
- **THEN** recibe la ficha completa con sus ejemplares
- **AND** cada ejemplar indica biblioteca, sucursal, signatura, tipo y soporte
- **AND** la ficha incluye `fuente`, `record_id` y `source_url` con la ficha original del OPAC de esa fuente
- **AND** la ficha incluye `paises_origen` como lista de códigos ISO

#### Scenario: Ficha inexistente

- **WHEN** el cliente solicita un `record_id` que no existe
- **THEN** la API responde con código 404
- **AND** devuelve un mensaje de error legible

#### Scenario: Compatibilidad con TITN de Madrid

- **WHEN** un cliente antiguo solicita `/api/records/2101557`
- **THEN** la API resuelve la edición de Madrid con ese `TITN`
- **AND** la respuesta conserva los campos existentes y añade `record_id` y `fuente`

### Requirement: Ubicaciones filtrables

La API SHALL exponer `GET /api/locations` con las redes y sucursales que tienen ejemplares. Cada ubicación SHALL incluir un código estable con prefijo y fuente (`b:<fuente>:<biblioteca>` para biblioteca, `s:<fuente>:<sucursal>` para sucursal), nombre visible, tipo, fuente, biblioteca matriz, municipio y número de ejemplares.

#### Scenario: Listado de ubicaciones

- **WHEN** el cliente solicita `/api/locations`
- **THEN** recibe una entrada `b:<fuente>:<biblioteca_codigo>` por cada red
- **AND** recibe una entrada `s:<fuente>:<sucursal_codigo>` por cada sucursal con ejemplares
- **AND** cada sucursal incluye su fuente, el código y nombre de su biblioteca matriz

#### Scenario: Misma ubicación en dos fuentes

- **WHEN** dos fuentes tienen una biblioteca o sucursal con el mismo código
- **THEN** la API devuelve dos entradas con códigos distintos
- **AND** cada una indica su fuente

### Requirement: Recursos de lista

La API SHALL exponer `POST /api/lists`, `GET /api/lists/{token}`, `POST /api/lists/{token}/items`, `DELETE /api/lists/{token}/items/{record_id}` y `PATCH /api/lists/{token}`. El token SHALL actuar como credencial de lectura y edición y SHALL almacenarse hasheado. Las mutaciones de elementos SHALL devolver el número actualizado de elementos.

#### Scenario: Crear una lista

- **WHEN** el cliente envía `POST /api/lists`
- **THEN** la API crea una lista vacía
- **AND** devuelve el token una sola vez
- **AND** en la base de datos solo queda el hash del token

#### Scenario: Consultar una lista

- **WHEN** el cliente solicita `GET /api/lists/{token}` con un token válido
- **THEN** recibe el título, las fechas, el número de elementos y los elementos de la lista

#### Scenario: Anadir y quitar elementos

- **WHEN** el cliente envía `POST /api/lists/{token}/items` con un `record_id`
- **THEN** la edición se añade si no estaba
- **AND** una segunda petición con el mismo `record_id` no duplica la entrada
- **AND** `DELETE /api/lists/{token}/items/{record_id}` la elimina
- **AND** la respuesta incluye el número actualizado de elementos

#### Scenario: Anadir una edicion inexistente

- **WHEN** el cliente envía un `record_id` que no existe en el catálogo
- **THEN** la API responde con 422
- **AND** la lista no cambia

#### Scenario: Compatibilidad con TITN de Madrid

- **WHEN** un cliente antiguo envía o elimina un `titn` sin fuente
- **THEN** la API lo resuelve como `madrid:<titn>`
- **AND** la lista se comporta igual que con el `record_id` completo

#### Scenario: Token invalido

- **WHEN** el cliente usa un token desconocido o caducado
- **THEN** la API responde con 404
- **AND** no revela si la lista existió

### Requirement: Forma de la respuesta de lista

La respuesta de una lista SHALL incluir su título, fechas, número de elementos y cada elemento con `record_id`, `fuente`, `titn`, título vigente o guardado, soportes, año, portada y URL del OPAC cuando existan. Los elementos SHALL devolverse del más reciente al más antiguo.

#### Scenario: Lista con elementos disponibles

- **WHEN** el cliente consulta una lista con ediciones presentes en el catálogo
- **THEN** cada elemento incluye los datos vigentes de la edición
- **AND** incluye su `record_id`, su `fuente` y la URL de su ficha en el OPAC

#### Scenario: Orden de los elementos

- **WHEN** el cliente consulta una lista con varios elementos
- **THEN** los recibe ordenados del más reciente al más antiguo

#### Scenario: Elemento sin ficha vigente

- **WHEN** una edición guardada ya no existe en el catálogo
- **THEN** el elemento incluye el título guardado y su `record_id`
- **AND** indica que la ficha no está disponible
- **AND** la lista sigue respondiendo con el resto de elementos
