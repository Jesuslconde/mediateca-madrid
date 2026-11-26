# portal-web Specification

## Purpose
Ofrecer un portal alternativo donde cualquier persona pueda buscar vídeos, distinguir DVD de Blu-ray y consultar en qué bibliotecas está disponible cada ejemplar.

## Requirements

### Requirement: Página de inicio con búsqueda

El portal MUST mostrar un buscador principal y accesos rápidos a los filtros `Solo DVD` y `Solo Blu-ray`.

#### Scenario: Acceso rápido a Blu-ray

- **WHEN** el usuario pulsa `Solo Blu-ray`
- **THEN** se abre la búsqueda con `soporte=Blu-ray`
- **AND** los resultados muestran la faceta de soporte activa

### Requirement: Resultados y facetas

La página de resultados MUST mostrar título, año, soportes, géneros, países de origen y bibliotecas tenedoras, y SHALL incluir filtros laterales combinables por soporte, género, idioma, país de origen, año y biblioteca o sucursal. SHALL NOT ofrecer un filtro por disponibilidad. El selector de ubicación SHALL agrupar las sucursales bajo su biblioteca matriz, SHALL permitir buscar por nombre visible y SHALL enviar un código estable en el parámetro `biblioteca`.

#### Scenario: Combinar filtros

- **WHEN** el usuario marca `DVD` y una biblioteca o sucursal
- **THEN** la lista se actualiza con los registros que cumplen ambos filtros
- **AND** se conserva el término de búsqueda
- **AND** no aparece ninguna opción «Solo disponible»

#### Scenario: Filtrar por sucursal

- **WHEN** el usuario escribe `Luis Martín Santos` en el selector de ubicación
- **THEN** aparece la sucursal agrupada bajo `MADRID. Bibliotecas Públicas`
- **AND** al seleccionarla se envía su código estable
- **AND** el filtro activo muestra el nombre visible de la sucursal

#### Scenario: Filtrar por país de origen

- **WHEN** el usuario selecciona un país en el filtro lateral
- **THEN** la lista se actualiza con las ediciones que incluyen ese país
- **AND** el filtro se combina con el término de búsqueda y el resto de filtros
- **AND** el país seleccionado aparece como filtro activo

#### Scenario: Varios países seleccionados

- **WHEN** el usuario selecciona más de un país
- **THEN** la lista incluye las ediciones que contienen cualquiera de los países seleccionados
- **AND** se conservan los demás filtros

### Requirement: Ficha de registro

La ficha MUST mostrar título, título uniforme, año, duración, idioma, país del OPAC, países de origen de TMDB, sinopsis, géneros, materias, personas con rol, enlaces externos, la fuente del registro y acceso a la ficha del OPAC correspondiente. SHALL NOT mostrar un estado de préstamo propio.

#### Scenario: Ficha de una película

- **WHEN** el usuario abre una película
- **THEN** ve su sinopsis, dirección, reparto y duración
- **AND** ve la lista de bibliotecas tenedoras con signatura y soporte
- **AND** dispone de un enlace a la ficha original del OPAC de su fuente

#### Scenario: Ficha con países de TMDB

- **WHEN** la edición tiene países de origen obtenidos de TMDB
- **THEN** la ficha los muestra con su etiqueta en español
- **AND** el país del OPAC se sigue mostrando por separado

#### Scenario: Enlace al OPAC de otra fuente

- **WHEN** el usuario abre una edición de una fuente distinta de Madrid
- **THEN** el enlace al OPAC usa la URL de esa fuente
- **AND** no se construye con la URL de Madrid

### Requirement: Accesibilidad y estado vacío

El portal MUST ser navegable por teclado y SHALL mostrar un estado vacío claro cuando no haya resultados.

#### Scenario: Búsqueda sin resultados

- **WHEN** la búsqueda no devuelve registros
- **THEN** se muestra un mensaje con sugerencias
- **AND** se ofrece limpiar los filtros

### Requirement: Bibliotecas tenedoras y enlace al OPAC

La ficha SHALL agrupar los ejemplares por biblioteca y sucursal, indicar signatura, tipo y soporte, y enlazar cada biblioteca o la ficha del registro a la página del OPAC. SHALL NOT mostrar estado ni historial de préstamo.

#### Scenario: Biblioteca con Blu-ray

- **WHEN** una biblioteca posee un ejemplar Blu-ray del título
- **THEN** la ficha la muestra con la etiqueta `Blu-ray`
- **AND** indica la signatura y la sucursal
- **AND** no muestra si está prestado o disponible

#### Scenario: Enlace al OPAC

- **WHEN** el usuario pulsa el enlace de la ficha del OPAC
- **THEN** se abre en una pestaña nueva la ficha original del registro
- **AND** allí puede consultar el estado de préstamo actualizado

### Requirement: Atribución de TMDB

El portal MUST mostrar la atribución de TMDB que exigen sus condiciones de uso en todas las páginas que presentan países de origen obtenidos de TMDB.

#### Scenario: Atribución visible

- **WHEN** el usuario consulta una página con datos de TMDB
- **THEN** el portal muestra el texto de atribución de TMDB
- **AND** el texto no se oculta con los filtros ni con la paginación

### Requirement: Selección de código postal

La ficha SHALL ofrecer un selector de código postal para establecer la referencia de cercanía, SHALL recordar la elección entre visitas y SHALL permitir limpiarla. SHALL NOT solicitar geolocalización del navegador.

#### Scenario: Seleccionar un código postal

- **WHEN** el usuario elige un código postal en la ficha
- **THEN** la ficha usa ese código postal como referencia de cercanía
- **AND** no se solicita permiso de geolocalización

#### Scenario: Recordar la elección

- **WHEN** el usuario vuelve a abrir una ficha después de haber elegido un código postal
- **THEN** la ficha restaura esa elección
- **AND** mantiene el orden por cercanía

#### Scenario: Limpiar la elección

- **WHEN** el usuario limpia el código postal
- **THEN** la ficha deja de usar una referencia de cercanía
- **AND** vuelve al orden alfabético

#### Scenario: Código postal desconocido

- **WHEN** la elección guardada no corresponde a ningún código postal disponible
- **THEN** la ficha ignora esa elección
- **AND** muestra el orden alfabético

### Requirement: Orden por cercanía

Con un código postal seleccionado, la ficha SHALL ordenar las bibliotecas por distancia aproximada y SHALL mostrar esa distancia. Las bibliotecas sin ubicación SHALL quedar al final; si ninguna tiene ubicación, SHALL mantener el orden alfabético y avisar.

#### Scenario: Orden y distancia

- **WHEN** el usuario selecciona un código postal y las bibliotecas tienen ubicación
- **THEN** la ficha ordena las bibliotecas de menor a mayor distancia aproximada
- **AND** muestra la distancia junto a cada biblioteca

#### Scenario: Sucursal con código postal sin coordenadas

- **WHEN** una sucursal tiene código postal pero no coordenadas
- **THEN** la ficha usa el centroide de ese código postal como su ubicación
- **AND** la incluye en el orden por cercanía

#### Scenario: Bibliotecas sin ubicación

- **WHEN** algunas bibliotecas no tienen coordenadas ni código postal utilizable
- **THEN** esas bibliotecas quedan al final del orden
- **AND** se ordenan alfabéticamente entre ellas

#### Scenario: Ninguna ubicación disponible

- **WHEN** ninguna biblioteca de la ficha tiene ubicación utilizable
- **THEN** la ficha mantiene el orden alfabético
- **AND** muestra un aviso de que no hay datos de ubicación disponibles

#### Scenario: Sin código postal

- **WHEN** no hay un código postal seleccionado
- **THEN** la ficha mantiene el orden alfabético actual

### Requirement: Atribución de códigos postales

El portal MUST mostrar en la ficha la atribución de las fuentes de los centroides de códigos postales utilizados para calcular las distancias.

#### Scenario: Atribución visible

- **WHEN** el usuario consulta una ficha con ordenación por cercanía disponible
- **THEN** el portal muestra la atribución de las fuentes de los códigos postales
- **AND** la atribución no se oculta al ordenar las bibliotecas

### Requirement: Navegación sin recarga completa

El portal SHALL navegar entre la portada, los resultados y la ficha sin recargar el documento completo. Buscar y aplicar filtros MUST actualizar los resultados mediante navegación cliente y MUST mantener los parámetros en la URL. Los enlaces internos a fichas SHALL usar `record_id`.

#### Scenario: Buscar desde la portada

- **WHEN** el usuario envía una búsqueda desde la portada
- **THEN** se muestran los resultados sin recargar el documento completo
- **AND** la URL contiene el término de búsqueda y puede compartirse

#### Scenario: Aplicar filtros

- **WHEN** el usuario cambia un filtro y lo aplica
- **THEN** los resultados se actualizan sin recargar el documento completo
- **AND** la URL conserva el término, los filtros y el orden activos

#### Scenario: Abrir una ficha desde resultados

- **WHEN** el usuario abre un resultado
- **THEN** la URL de la ficha incluye el `record_id` completo
- **AND** la navegación conserva el estado previo de la búsqueda

### Requirement: Ordenación inmediata en resultados

La página de resultados SHALL mostrar un selector de orden en la cabecera. Al cambiar el orden MUST actualizar los resultados de inmediato, conservar la consulta y los filtros y volver a la primera página.

#### Scenario: Ordenar por año descendente

- **WHEN** el usuario selecciona «Año (más reciente)» en la cabecera de resultados
- **THEN** los resultados se actualizan sin pulsar «Aplicar filtros»
- **AND** la consulta y los filtros activos se conservan
- **AND** la paginación vuelve a la primera página

#### Scenario: Orden compartido por URL

- **WHEN** el usuario abre una URL de resultados que incluye un orden
- **THEN** la página muestra los resultados en ese orden
- **AND** el selector de la cabecera refleja el orden activo

### Requirement: Estado de carga visible

Al navegar a resultados o a la ficha, el portal SHALL mostrar un estado de carga visible sin bloquear la interfaz.

#### Scenario: Cambio de búsqueda

- **WHEN** el usuario envía una nueva búsqueda o cambia un filtro
- **THEN** se muestra un esqueleto de resultados mientras llega la respuesta
- **AND** la interfaz sigue siendo utilizable

#### Scenario: Cambio de página

- **WHEN** el usuario pulsa la paginación
- **THEN** el enlace muestra un estado pendiente hasta que se cargan los resultados

### Requirement: Vuelta a la búsqueda con el estado previo

El enlace de vuelta de la ficha SHALL devolver a la búsqueda con el término, los filtros, el orden y la página previos. Si no hay estado previo, SHALL volver a la búsqueda sin filtros.

#### Scenario: Volver desde una ficha abierta en los resultados

- **WHEN** el usuario abre una ficha desde una búsqueda con filtros y orden
- **THEN** el enlace de vuelta abre esa misma búsqueda
- **AND** conserva el término, los filtros, el orden y la página

#### Scenario: Abrir una ficha sin búsqueda previa

- **WHEN** el usuario abre una ficha directamente sin estado de búsqueda previo
- **THEN** el enlace de vuelta abre la búsqueda sin filtros

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

### Requirement: Compatibilidad de URLs de registro

El portal SHALL seguir aceptando las URLs antiguas `/registro/{titn}` y SHALL resolverlas como la edición de Madrid con ese `TITN`. La ficha SHALL mostrar la URL canónica con `record_id` sin romper los enlaces compartidos existentes.

#### Scenario: Enlace antiguo de Madrid

- **WHEN** un usuario abre `/registro/2101557`
- **THEN** la ficha de la edición de Madrid se muestra correctamente
- **AND** el enlace compartible usa el `record_id` canónico

#### Scenario: Enlace antiguo inexistente

- **WHEN** un usuario abre una URL antigua cuyo `TITN` no existe en Madrid
- **THEN** el portal muestra el estado de ficha no encontrada
- **AND** no busca ese `TITN` en otras fuentes

### Requirement: Fuente visible en la ficha

La ficha SHALL identificar la fuente del registro con su nombre visible. Con una sola fuente activa SHALL mostrar la etiqueta sin ofrecer un selector; el selector de fuentes se incorporará cuando existan varias fuentes visibles.

#### Scenario: Ficha de Madrid

- **WHEN** el usuario abre una edición de Madrid
- **THEN** la ficha muestra la etiqueta de la fuente Madrid
- **AND** no muestra un selector de comunidad

#### Scenario: Fuente desconocida

- **WHEN** la edición declara una fuente que ya no existe o está deshabilitada
- **THEN** la ficha sigue mostrando el registro
- **AND** identifica la fuente por su código sin inventar un nombre

### Requirement: Una tarjeta por obra

La página de resultados MUST mostrar una única tarjeta por obra. La tarjeta SHALL indicar el número de ediciones, la unión de soportes y los datos agregados de ejemplares y bibliotecas. La cabecera SHALL distinguir el número de obras del número de ediciones.

#### Scenario: Película con varias ediciones
- **WHEN** el usuario busca una película con cuatro ediciones en la misma obra
- **THEN** ve una sola tarjeta
- **AND** la tarjeta indica que hay cuatro ediciones
- **AND** muestra todos los soportes disponibles entre esas ediciones

#### Scenario: Cabecera con totales
- **WHEN** el usuario consulta resultados agrupados
- **THEN** la cabecera muestra el número de obras y el número de ediciones
- **AND** la paginación corresponde al número de obras

#### Scenario: Edición sin obra
- **WHEN** una edición no pertenece a ninguna obra
- **THEN** aparece en su propia tarjeta
- **AND** la tarjeta indica una sola edición

### Requirement: Ediciones de la misma obra en la ficha

La ficha de registro SHALL mostrar una sección con todas las ediciones de la misma obra, indicando título, año, soportes y número de ejemplares, y SHALL enlazar cada edición a su propia ficha.

#### Scenario: Ficha con varias ediciones
- **WHEN** el usuario abre una edición que tiene ediciones hermanas
- **THEN** la ficha muestra la lista de ediciones de la obra
- **AND** cada entrada enlaza a su `/registro/{record_id}`
- **AND** se distingue la edición que está abierta

#### Scenario: Ficha con una sola edición
- **WHEN** la edición es la única de su obra
- **THEN** la ficha no muestra la sección de ediciones hermanas
- **AND** el resto de la ficha no cambia

### Requirement: Presentación de fuentes de cobertura

El portal SHALL mostrar los resultados y las fichas de fuentes de cobertura con título, año, soportes, géneros y enlace al catálogo oficial, aunque no tengan bibliotecas tenedoras. En ausencia de un filtro de biblioteca SHALL NOT ocultar esos registros ni ofrecer un filtro de disponibilidad.

#### Scenario: Resultado sin bibliotecas

- **WHEN** un resultado pertenece a una fuente de cobertura sin ejemplares
- **THEN** se muestra con su título, año y soportes
- **AND** se ofrece el enlace a su catálogo oficial
- **AND** no se muestra una lista de bibliotecas tenedoras

#### Scenario: Ficha sin bibliotecas

- **WHEN** el usuario abre la ficha de una edición de cobertura
- **THEN** ve sus metadatos y el enlace al catálogo oficial
- **AND** ve un estado vacío de bibliotecas en lugar de un error

#### Scenario: Enlace al catálogo de la fuente

- **WHEN** el usuario pulsa el enlace de la ficha de una edición de cobertura
- **THEN** se abre la URL permanente del catálogo de esa fuente
- **AND** no se usa la URL de Madrid ni una URL global

#### Scenario: Filtro de biblioteca

- **WHEN** el usuario aplica un filtro de biblioteca o sucursal
- **THEN** las ediciones de cobertura sin esa biblioteca no aparecen en el resultado filtrado
- **AND** siguen apareciendo cuando no hay filtro de biblioteca

### Requirement: Selector global de código postal

El portal SHALL ofrecer un selector global de código postal para toda España, con autocompletado por código o municipio. La elección SHALL recordarse entre visitas y SHALL reflejarse en la URL de búsqueda. SHALL NOT solicitar geolocalización del navegador.

#### Scenario: Elegir un código postal

- **WHEN** el usuario escribe su código postal o su municipio en el selector global
- **THEN** puede elegir un código postal de toda España
- **AND** no se solicita permiso de geolocalización

#### Scenario: Recordar la elección

- **WHEN** el usuario vuelve al portal después de haber elegido un código postal
- **THEN** el selector restaura esa elección
- **AND** la ficha y la búsqueda la usan como referencia

#### Scenario: Código postal en la URL

- **WHEN** el usuario busca con un código postal elegido
- **THEN** la URL de búsqueda incluye `cp`
- **AND** la URL puede compartirse y abre la misma referencia

### Requirement: Control de radio

La página de resultados SHALL ofrecer un control de radio con opciones predefinidas y una opción sin límite. El radio SHALL combinarse con el código postal y el resto de filtros.

#### Scenario: Aplicar un radio

- **WHEN** el usuario elige un radio con un código postal seleccionado
- **THEN** los resultados se limitan a las sucursales dentro de ese radio
- **AND** el radio aparece en la URL y como filtro activo

#### Scenario: Sin límite

- **WHEN** el usuario elige la opción sin límite
- **THEN** la búsqueda no se acota por distancia
- **AND** se conservan el código postal y el resto de filtros

### Requirement: Selección de bibliotecas cercanas

Con un código postal y un radio, el portal SHALL mostrar las bibliotecas y sucursales resultantes y SHALL permitir buscar en todas, excluir algunas o buscar solo en una.

#### Scenario: Lista de bibliotecas cercanas

- **WHEN** el usuario fija un código postal y un radio
- **THEN** el portal muestra las bibliotecas y sucursales dentro del radio con su distancia
- **AND** puede marcarlas o desmarcarlas

#### Scenario: Excluir bibliotecas

- **WHEN** el usuario desmarca una o varias bibliotecas del conjunto cercano
- **THEN** la búsqueda se limita al resto
- **AND** las excluidas se reflejan en la URL

#### Scenario: Buscar solo en una

- **WHEN** el usuario elige buscar solo en una biblioteca concreta
- **THEN** la búsqueda se limita a esa biblioteca
- **AND** el filtro usa el código estable de la biblioteca o sucursal
