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
