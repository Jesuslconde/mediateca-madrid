# api-portal Specification

## Purpose
Exponer los datos normalizados y el índice de búsqueda mediante una API HTTP estable para que el portal web y otros clientes puedan consultar el catálogo.

## Requirements

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

### Requirement: Bibliotecas y estadísticas

La API SHALL exponer la lista de bibliotecas con su número de ejemplares y estadísticas agregadas por soporte, sin contadores de disponibilidad de préstamo.

#### Scenario: Listado de bibliotecas

- **WHEN** el cliente solicita `/api/libraries`
- **THEN** recibe las bibliotecas conocidas con su municipio y número de ejemplares
- **AND** no recibe contadores de ejemplares disponibles

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

### Requirement: Búsqueda agrupada por obra

`GET /api/search` MUST devolver como máximo un resultado por obra. Cada resultado SHALL indicar `obra_id`, `obra_titulo`, el número de ediciones y los datos agregados de soportes, bibliotecas y ejemplares. La respuesta SHALL incluir el total de obras y el total de ediciones.

#### Scenario: Resultado con varias ediciones
- **WHEN** el cliente busca un título que tiene varias ediciones en una obra
- **THEN** recibe un único resultado para la obra
- **AND** el resultado incluye `obra_id`, `obra_titulo` y `ediciones_count`
- **AND** `soportes`, `bibliotecas` y `ejemplares` agregan todas las ediciones de la obra

#### Scenario: Resultado sin obra
- **WHEN** una edición no tiene obra
- **THEN** aparece como un resultado propio
- **AND** `ediciones_count` vale `1`

#### Scenario: Totales de la búsqueda
- **WHEN** el cliente consulta `/api/search`
- **THEN** la respuesta incluye `total` con el número de obras
- **AND** incluye `total_ediciones` con el número de ediciones
- **AND** las facetas siguen contando ediciones

### Requirement: Ediciones de la obra en la ficha

`GET /api/records/{record_id}` SHALL incluir, cuando la edición tenga obra, la lista de ediciones de esa obra con `record_id`, `fuente`, `titn`, título, año, soportes, `ean`, número de ejemplares y `source_url`.

#### Scenario: Ficha con ediciones hermanas
- **WHEN** el cliente solicita una edición que pertenece a una obra con varias ediciones
- **THEN** la respuesta incluye la lista de ediciones de la obra
- **AND** cada edición conserva su `record_id`, su fuente y su URL del OPAC

#### Scenario: Ficha sin ediciones hermanas
- **WHEN** la edición no tiene obra o es la única edición de su obra
- **THEN** la lista de ediciones contiene como máximo la edición actual
- **AND** la ficha sigue siendo válida

#### Scenario: Compatibilidad de la ficha
- **WHEN** un cliente anterior consume una ficha
- **THEN** sigue recibiendo los campos existentes
- **AND** los nuevos campos de ediciones son opcionales

### Requirement: Parámetros de proximidad en la búsqueda

`GET /api/search` SHALL aceptar `cp` (código postal de cinco dígitos), `radio_km` (número positivo) y `excluir` (repetible, códigos de ubicación). `radio_km` SHALL requerir un `cp` resoluble. La API SHALL devolver 422 cuando `radio_km` se envíe sin `cp` o con un `cp` no resoluble.

#### Scenario: Búsqueda acotada por radio

- **WHEN** el cliente solicita `/api/search?cp=28015&radio_km=5`
- **THEN** recibe solo las ediciones con ejemplares en sucursales dentro de 5 km
- **AND** los totales y las facetas se calculan sobre ese conjunto

#### Scenario: Radio sin código postal

- **WHEN** el cliente solicita `/api/search?radio_km=5` sin `cp`
- **THEN** la API responde con 422
- **AND** indica que `radio_km` requiere `cp`

#### Scenario: Código postal no resoluble

- **WHEN** el cliente solicita `/api/search?cp=00000&radio_km=5`
- **THEN** la API responde con 422
- **AND** indica que el código postal no se puede resolver

#### Scenario: Código postal sin radio

- **WHEN** el cliente solicita `/api/search?cp=28015` sin `radio_km`
- **THEN** la búsqueda no se acota por distancia
- **AND** se comporta como una búsqueda sin proximidad

#### Scenario: Excluir ubicaciones

- **WHEN** el cliente solicita `/api/search?cp=28015&radio_km=5&excluir=s:madrid:BMALC1`
- **THEN** se excluyen las ediciones que solo tienen ejemplares en esa sucursal
- **AND** el resto de la búsqueda se mantiene

### Requirement: Ubicaciones con coordenadas y distancia

`GET /api/locations` SHALL incluir por ubicación su código postal, latitud y longitud cuando estén disponibles. SHALL aceptar `cp` y `radio_km` opcionales para devolver solo las ubicaciones cercanas, con su distancia aproximada en kilómetros.

#### Scenario: Listado con coordenadas

- **WHEN** el cliente solicita `/api/locations`
- **THEN** cada ubicación incluye su código postal, latitud y longitud cuando estén disponibles
- **AND** los campos de ubicación son opcionales

#### Scenario: Ubicaciones cercanas

- **WHEN** el cliente solicita `/api/locations?cp=28015&radio_km=5`
- **THEN** recibe solo las ubicaciones dentro de 5 km
- **AND** cada una incluye su distancia aproximada en kilómetros
- **AND** se ordenan de menor a mayor distancia

#### Scenario: Distancia sin referencia

- **WHEN** el cliente solicita `/api/locations` sin `cp` ni `radio_km`
- **THEN** las ubicaciones no incluyen distancia
- **AND** se mantienen el orden y los campos anteriores
