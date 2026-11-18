# Spec Delta

## ADDED Requirements

### Requirement: Accion de favorito

Los resultados y la ficha SHALL ofrecer una accion de favorito que anada o quite la edicion de la lista activa. La accion SHALL reflejar el estado guardado, ser operable por teclado y actualizar la interfaz sin recargar el documento.

#### Scenario: Guardar desde los resultados

- **WHEN** el usuario pulsa el corazon de un resultado
- **THEN** la edicion se guarda en la lista activa
- **AND** el corazon pasa a estado guardado sin recargar la pagina
- **AND** se conservan el termino, los filtros, el orden y la pagina

#### Scenario: Quitar desde la ficha

- **WHEN** el usuario pulsa el corazon de una edicion ya guardada en su ficha
- **THEN** la edicion se quita de la lista
- **AND** el corazon vuelve a estado no guardado

#### Scenario: Estado tras recargar

- **WHEN** el usuario recarga una pagina de resultados o una ficha
- **THEN** el corazon muestra el estado real de cada edicion en la lista activa

#### Scenario: Uso con teclado

- **WHEN** el usuario navega con teclado hasta el corazon y lo activa
- **THEN** la accion se ejecuta
- **AND** el estado y la etiqueta accesible anuncian si la edicion esta guardada

#### Scenario: Lista llena

- **WHEN** el usuario intenta guardar una edicion en una lista con 200 elementos
- **THEN** el portal muestra un aviso de lista llena
- **AND** el corazon no queda en estado guardado
- **AND** la lista no cambia

### Requirement: Pagina Mi lista

El portal SHALL ofrecer `/mi-lista` con los titulos guardados, el enlace compartible, el recuento y acciones para quitar elementos y renombrar la lista. Sin lista activa SHALL mostrar un estado vacio con la accion de crear una.

#### Scenario: Sin lista activa

- **WHEN** el usuario abre `/mi-lista` sin cookie de lista
- **THEN** ve un estado vacio explicando que puede guardar titulos con el corazon
- **AND** puede crear una lista vacia de forma explicita

#### Scenario: Cookie con una lista que ya no existe

- **WHEN** el usuario abre `/mi-lista` con una cookie cuyo token ya no existe
- **THEN** el portal lo trata como si no hubiera lista activa
- **AND** muestra el estado vacio
- **AND** el siguiente favorito crea una lista nueva

#### Scenario: Lista con elementos

- **WHEN** el usuario abre `/mi-lista` con una lista activa
- **THEN** ve los titulos guardados y su recuento
- **AND** puede quitar elementos
- **AND** puede renombrar la lista

#### Scenario: Enlace compartible visible

- **WHEN** el usuario abre `/mi-lista` con una lista activa
- **THEN** ve el enlace `/lista/{token}` y puede copiarlo
- **AND** se advierte de que cualquiera con el enlace puede editar

### Requirement: Pagina de lista compartida

El portal SHALL ofrecer `/lista/{token}` para consultar y editar una lista compartida, con el mismo contenido y acciones que Mi lista. Al abrirla, SHALL adoptarla como lista activa del navegador.

#### Scenario: Abrir un enlace compartido

- **WHEN** una persona abre un enlace de lista valido
- **THEN** ve el titulo, el recuento y los elementos de la lista
- **AND** puede anadir, quitar y renombrar
- **AND** la lista pasa a ser su lista activa

#### Scenario: Enlace desconocido

- **WHEN** una persona abre un enlace con un token desconocido o caducado
- **THEN** el portal muestra una pagina de lista no encontrada
- **AND** ofrece volver a la busqueda

### Requirement: Acceso a la lista desde la cabecera

La cabecera SHALL incluir un acceso a la lista activa con el numero de elementos guardados.

#### Scenario: Recuento actualizado

- **WHEN** el usuario guarda o quita un favorito
- **THEN** el recuento de la cabecera refleja el nuevo total
- **AND** el acceso abre `/mi-lista`

#### Scenario: Sin lista activa

- **WHEN** el navegador no tiene lista activa
- **THEN** la cabecera muestra el acceso sin recuento o con cero
- **AND** al abrirlo se ofrece crear la lista
