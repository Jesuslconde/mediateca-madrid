# Spec Delta

## MODIFIED Requirements

### Requirement: Gestión de sesión del OPAC

El recolector MUST iniciar una sesión válida contra el OPAC de la fuente, conservar cookies y extraer el identificador de sesión de la ruta según el perfil de esa fuente antes de consultar resultados o fichas. Cada fuente SHALL mantener su propia sesión, cookies y contadores de captcha.

#### Scenario: Renovación de sesión caducada

- **WHEN** una petición devuelve la página de sesión expirada o un error de sesión
- **THEN** el recolector renueva la sesión y reintenta la petición una vez
- **AND** registra el evento sin abortar el lote completo

#### Scenario: Sesión de otra fuente activa

- **WHEN** una fuente renueva su sesión
- **THEN** la sesión de las demás fuentes no se modifica
- **AND** sus cookies y contadores siguen separados

### Requirement: Búsqueda por formato vídeo

El recolector SHALL consultar el formulario avanzado con el filtro de formato declarado por la fuente y SHALL recorrer la paginación de resultados hasta el límite configurado. El filtro de Madrid (`Videos y DVD`) y el de otra fuente SHALL poder diferir sin cambiar el flujo de recolección.

#### Scenario: Recolección de una consulta

- **WHEN** se ejecuta una recolección con una consulta y un límite de páginas
- **THEN** se obtienen las fichas de detalle de los resultados
- **AND** se registra el número de registros procesados y los errores

#### Scenario: Filtro de formato por fuente

- **WHEN** una fuente declara un valor de filtro de vídeo distinto del de Madrid
- **THEN** la búsqueda usa el valor de esa fuente
- **AND** no se reutiliza el valor de Madrid

### Requirement: Actualización incremental

El sistema SHALL soportar descubrimientos incrementales por fuente, reutilizando el `cursor_doc` y `cursor_titn` del último descubrimiento completado de esa fuente, y SHALL programar un barrido completo periódico como red de seguridad.

#### Scenario: Novedades de vídeos

- **WHEN** se ejecuta la recolección incremental de una fuente
- **THEN** solo se procesan los registros nuevos o modificados de esa fuente en el periodo configurado
- **AND** el resto del catálogo permanece intacto

#### Scenario: Sin descubrimiento previo

- **WHEN** se solicita un descubrimiento incremental de una fuente y no hay un descubrimiento completado de esa fuente
- **THEN** se ejecuta un descubrimiento completo de esa fuente
- **AND** queda registrado como modo `full`

#### Scenario: Barrido completo de seguridad

- **WHEN** se cumple el intervalo de barrido completo de una fuente
- **THEN** se ejecuta un descubrimiento completo de esa fuente aunque exista un cursor incremental
- **AND** se actualizan las marcas de última visualización y las ausencias solo en esa fuente

### Requirement: Checkpoint de descubrimiento

El descubrimiento MUST guardar el último `DOC` y el último `TITN` procesados de la fuente y SHALL reanudar desde ese punto tras una interrupción, sin compartir cursores con otras fuentes.

#### Scenario: Reanudar tras fallo

- **WHEN** el descubrimiento de una fuente se interrumpe en el registro 20.000
- **THEN** el siguiente trabajo de esa fuente empieza en el `DOC` guardado
- **AND** verifica que el primer `TITN` coincide con el cursor

#### Scenario: Cursores independientes

- **WHEN** dos fuentes tienen descubrimientos en curso
- **THEN** cada una usa su propio `cursor_doc` y `cursor_titn`
- **AND** el avance de una no altera el de la otra

## ADDED Requirements

### Requirement: Separación de catálogos en la recolección

Cada ejecución de descubrimiento o enriquecimiento MUST pertenecer a una única fuente. Los registros, bibliotecas, sucursales y ejemplares creados SHALL quedar asociados a esa fuente y SHALL NOT reutilizar entidades de otra fuente por coincidencia de código.

#### Scenario: Recolección de una fuente

- **WHEN** se ejecuta un descubrimiento de una fuente
- **THEN** todos los stubs creados quedan asociados a esa fuente
- **AND** no se crean ediciones de otras fuentes

#### Scenario: Enriquecimiento de una fuente

- **WHEN** se enriquece un lote de una fuente
- **THEN** solo se seleccionan ediciones pendientes de esa fuente
- **AND** sus ejemplares quedan bajo la fuente correcta
