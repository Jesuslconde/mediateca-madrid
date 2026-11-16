# Spec Delta

## ADDED Requirements

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
