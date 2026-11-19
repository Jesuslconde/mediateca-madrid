# Spec Delta

## MODIFIED Requirements

### Requirement: Pagina Mi lista

El portal SHALL ofrecer `/mi-lista` con los titulos guardados, el enlace compartible, el recuento y acciones para quitar elementos y renombrar la lista. Sin lista activa SHALL mostrar un estado vacio con la accion de crear una. La pagina SHALL usar la lista activa persistente del navegador y MUST mostrar la misma lista en todas las pestanas y tras reabrir el navegador.

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

#### Scenario: Varias pestanas abren Mi lista

- **WHEN** el usuario abre `/mi-lista` en varias pestanas del mismo navegador
- **THEN** todas muestran la misma lista y el mismo recuento
- **AND** los cambios se reflejan al recargar o navegar en cualquiera de ellas

#### Scenario: Reapertura del navegador

- **WHEN** el usuario cierra el navegador y vuelve a abrir `/mi-lista`
- **THEN** ve la lista activa que tenia antes de cerrar
- **AND** no se le ofrece crear una lista nueva

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

#### Scenario: Adopcion compartida entre pestanas

- **WHEN** una persona abre un enlace de lista en una pestana
- **THEN** esa lista pasa a ser la activa para todas las pestanas del navegador
- **AND** sigue siendo la activa al reabrir el navegador

### Requirement: Acceso a la lista desde la cabecera

La cabecera SHALL incluir un acceso a la lista activa con el numero de elementos guardados. El recuento MUST ser el de la lista activa del navegador y coincidir entre las pestanas que comparten esa lista.

#### Scenario: Recuento actualizado

- **WHEN** el usuario guarda o quita un favorito
- **THEN** el recuento de la cabecera refleja el nuevo total
- **AND** el acceso abre `/mi-lista`

#### Scenario: Sin lista activa

- **WHEN** el navegador no tiene lista activa
- **THEN** la cabecera muestra el acceso sin recuento o con cero
- **AND** al abrirlo se ofrece crear la lista

#### Scenario: Recuento compartido entre pestanas

- **WHEN** el usuario guarda o quita un favorito en una pestana
- **THEN** las demas pestanas muestran el recuento actualizado al recargar o navegar
- **AND** no abren una lista distinta
