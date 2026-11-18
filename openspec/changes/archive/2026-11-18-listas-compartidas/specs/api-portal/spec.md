# Spec Delta

## ADDED Requirements

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
