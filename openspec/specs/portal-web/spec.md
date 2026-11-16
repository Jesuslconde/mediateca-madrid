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

La página de resultados MUST mostrar título, año, soportes, géneros, países de origen y bibliotecas tenedoras, y SHALL incluir filtros laterales combinables por soporte, género, idioma, país de origen, año y biblioteca. SHALL NOT ofrecer un filtro por disponibilidad.

#### Scenario: Combinar filtros

- **WHEN** el usuario marca `DVD` y una biblioteca
- **THEN** la lista se actualiza con los registros que cumplen ambos filtros
- **AND** se conserva el término de búsqueda
- **AND** no aparece ninguna opción «Solo disponible»

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

La ficha MUST mostrar título, título uniforme, año, duración, idioma, país del OPAC, países de origen de TMDB, sinopsis, géneros, materias, personas con rol, enlaces externos y acceso a la ficha del OPAC. SHALL NOT mostrar un estado de préstamo propio.

#### Scenario: Ficha de una película

- **WHEN** el usuario abre una película
- **THEN** ve su sinopsis, dirección, reparto y duración
- **AND** ve la lista de bibliotecas tenedoras con signatura y soporte
- **AND** dispone de un enlace a la ficha original del OPAC

#### Scenario: Ficha con países de TMDB

- **WHEN** la edición tiene países de origen obtenidos de TMDB
- **THEN** la ficha los muestra con su etiqueta en español
- **AND** el país del OPAC se sigue mostrando por separado

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

El portal SHALL navegar entre la portada, los resultados y la ficha sin recargar el documento completo. Buscar y aplicar filtros MUST actualizar los resultados mediante navegación cliente y MUST mantener los parámetros en la URL.

#### Scenario: Buscar desde la portada

- **WHEN** el usuario envía una búsqueda desde la portada
- **THEN** se muestran los resultados sin recargar el documento completo
- **AND** la URL contiene el término de búsqueda y puede compartirse

#### Scenario: Aplicar filtros

- **WHEN** el usuario cambia un filtro y lo aplica
- **THEN** los resultados se actualizan sin recargar el documento completo
- **AND** la URL conserva el término, los filtros y el orden activos

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
