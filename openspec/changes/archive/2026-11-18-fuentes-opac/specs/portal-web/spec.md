# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
