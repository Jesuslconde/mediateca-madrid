# ingesta-catalogo Specification

## Purpose
Obtener de forma reproducible los registros de vídeos y DVD del OPAC AbsysNet de la Comunidad de Madrid, conservando el HTML original y los metadatos necesarios para reconstruir el índice sin volver a scrapear.

## Requirements

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

### Requirement: Límite de peticiones y reintentos

El recolector MUST aplicar un retardo configurable entre peticiones y MUST reintentar con backoff los errores temporales.

#### Scenario: Error temporal del servidor

- **WHEN** el OPAC responde con un error 5xx o un timeout
- **THEN** la petición se reintenta hasta el máximo configurado
- **AND** si persiste, la ficha se envía a una cola de fallidos

#### Scenario: Captcha sin FlareSolverr configurado

- **WHEN** el OPAC solicita un reCAPTCHA y no existe una URL efectiva de FlareSolverr
- **THEN** el recolector registra el captcha y detiene la petición
- **AND** el trabajo se reprograma según la política de reintentos existente
- **AND** no se intenta resolver el captcha por ningún otro medio

#### Scenario: Captcha con FlareSolverr no disponible

- **WHEN** el OPAC solicita un reCAPTCHA y FlareSolverr no responde o devuelve un error
- **THEN** el recolector registra el captcha fallido y detiene la petición
- **AND** el trabajo se reprograma con backoff
- **AND** no se repite la resolución del mismo captcha dentro de la misma petición

### Requirement: Resolución de captcha con FlareSolverr

El recolector MUST detectar la página de reCAPTCHA y, cuando exista una URL efectiva de FlareSolverr, resolver la misma petición a través de FlareSolverr y continuar con la respuesta obtenida. Si la resolución falla, MUST registrar el fallo y SHALL NOT entrar en un bucle de reintentos de captcha.

#### Scenario: Petición GET resuelta

- **WHEN** una petición GET recibe la página de reCAPTCHA y FlareSolverr está configurado
- **THEN** el recolector envía a FlareSolverr la misma URL, método y cookies de sesión
- **AND** usa el HTML y la URL final devueltos como respuesta de la petición
- **AND** continúa la recolección sin contar la petición como fallida

#### Scenario: Búsqueda POST resuelta

- **WHEN** la búsqueda del OPAC recibe un reCAPTCHA y FlareSolverr está configurado
- **THEN** el recolector envía a FlareSolverr el mismo método POST y los mismos datos de formulario
- **AND** conserva la sesión y los parámetros de búsqueda originales

#### Scenario: Cookies devueltas por FlareSolverr

- **WHEN** FlareSolverr resuelve una petición y devuelve cookies
- **THEN** el recolector incorpora esas cookies a su sesión del OPAC
- **AND** las peticiones posteriores las usan
- **AND** la paginación y el identificador de sesión siguen siendo válidos

#### Scenario: Respuesta que sigue siendo captcha

- **WHEN** la respuesta devuelta por FlareSolverr vuelve a contener el reCAPTCHA
- **THEN** el recolector la trata como resolución fallida
- **AND** no vuelve a invocar a FlareSolverr para esa misma petición
- **AND** registra el fallo para la política de reintentos del trabajo

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

### Requirement: Recolección sin estado de préstamo

El recolector MUST guardar la lista de bibliotecas y sucursales que poseen cada edición al crear o actualizar la ficha, y SHALL NOT consultar ni persistir el estado de préstamo de los ejemplares.

#### Scenario: Ficha procesada

- **WHEN** el recolector procesa la ficha de un activo
- **THEN** guarda sus ejemplares con biblioteca, sucursal, signatura, tipo y soporte
- **AND** no intenta determinar si cada ejemplar está prestado o disponible

#### Scenario: Actualización periódica

- **WHEN** se ejecuta una recolección periódica de fichas
- **THEN** se actualizan los metadatos y la lista de bibliotecas tenedoras
- **AND** no se ejecuta ninguna comprobación de disponibilidad de préstamo

#### Scenario: Ficha sin ejemplares

- **WHEN** la ficha no declara ejemplares
- **THEN** la edición se guarda sin bibliotecas tenedoras
- **AND** la recolección continúa sin error

### Requirement: Descubrimiento completo por truncamiento

El recolector MUST usar la consulta de truncamiento `*` con el filtro de formato `Videos y DVD` y SHALL recorrer toda la paginación hasta agotar los resultados.

#### Scenario: Catálogo completo

- **WHEN** se ejecuta el descubrimiento completo
- **THEN** se recorren todas las páginas de resultados
- **AND** se obtiene el conjunto de `TITN` de vídeo, DVD, Blu-ray, 4K UHD y VHS

#### Scenario: Orden estable

- **WHEN** el OPAC devuelve los resultados de `*`
- **THEN** el orden es `TITN` ascendente
- **AND** la paginación por `DOC` permite reanudar sin pérdidas

### Requirement: Parser de listado de resultados

El recolector MUST extraer de cada resultado el `TITN`, título, publicación, año, idioma, descripción física, géneros, materias y, cuando existan, autores y notas del MARC oculto. El título MUST ser el título propio visible, sin la mención de responsabilidad.

#### Scenario: Resultado con MARC oculto

- **WHEN** se parsea un `li.c-docs_unit`
- **THEN** se obtiene al menos `TITN`, título y descripción física
- **AND** se detecta el soporte desde `T300a`

#### Scenario: Título con mención de responsabilidad

- **WHEN** el resultado muestra `20.000 especies de abejas / dirección y guión de Estibaliz Urresola`
- **THEN** la edición guarda `20.000 especies de abejas`
- **AND** la mención de responsabilidad no forma parte del título

#### Scenario: Título con subtítulo en el listado

- **WHEN** el resultado muestra `Imágenes y justicia : el Derecho a través del cine /`
- **THEN** la edición guarda `Imágenes y justicia : el Derecho a través del cine`

### Requirement: Backfill de títulos normalizados

El sistema SHALL ofrecer un comando idempotente que recalcule los títulos de las ediciones existentes a partir de los metadatos MARC ya guardados, sin recolectar de nuevo el OPAC ni modificar las claves de agrupación de obras.

#### Scenario: Backfill en seco

- **WHEN** el operador ejecuta el backfill sin aplicar cambios
- **THEN** el comando informa de cuántas ediciones cambiarían y muestra ejemplos
- **AND** no modifica la base de datos

#### Scenario: Backfill aplicado

- **WHEN** el operador aplica el backfill
- **THEN** se actualizan `titulo` y `titulo_uniforme` de las ediciones afectadas
- **AND** no se crean ni modifican obras ni ejemplares

#### Scenario: Backfill idempotente

- **WHEN** el backfill se ejecuta dos veces seguidas
- **THEN** la segunda ejecución no encuentra títulos que cambiar

#### Scenario: Backfill con reindexado

- **WHEN** el operador aplica el backfill y solicita reindexar
- **THEN** las ediciones afectadas se envían al índice
- **AND** el resto del índice permanece intacto

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

### Requirement: Sesión durante paginación

Si la sesión caduca durante el descubrimiento, el recolector MUST reabrir sesión, repetir la búsqueda `*` y saltar al `DOC` actual.

#### Scenario: Sesión caducada en página profunda

- **WHEN** el OPAC devuelve la página de sesión expirada en `DOC=40001`
- **THEN** el cliente reabre sesión
- **AND** repite la búsqueda y continúa en el mismo `DOC`

### Requirement: Detección de altas y bajas

El descubrimiento SHALL marcar la fecha de última visualización de cada edición y SHALL identificar los `TITN` que han dejado de aparecer.

#### Scenario: Título nuevo

- **WHEN** aparece un `TITN` que no existía
- **THEN** se crea una edición stub
- **AND** queda pendiente de enriquecimiento

#### Scenario: Título desaparecido

- **WHEN** un `TITN` no aparece en un descubrimiento completo
- **THEN** se marca como no visto
- **AND** no se elimina automáticamente sin revisión

### Requirement: Enriquecimiento completo por lotes

El sistema MUST enriquecer todas las ediciones descubiertas en lotes de 5.000 por defecto, actualizando metadatos, créditos, materias y ejemplares.

#### Scenario: Lote de 5.000 fichas

- **WHEN** se ejecuta un trabajo de enriquecimiento
- **THEN** selecciona hasta 5.000 TITN pendientes
- **AND** al terminar el lote actualiza el cursor y las estadísticas

#### Scenario: Cobertura completa

- **WHEN** no quedan TITN con `detail_fetched_at` vacío
- **THEN** el trabajo termina y la cobertura de enriquecimiento es del 100%
- **AND** se registra en el estado de ingesta

### Requirement: Solo datos parseados

El enriquecimiento MUST persistir únicamente datos normalizados en PostgreSQL y MUST NOT guardar HTML crudo ni snapshots.

#### Scenario: Ficha procesada

- **WHEN** se enriquece un TITN
- **THEN** se guardan sus campos, personas, materias, enlaces y ejemplares
- **AND** no se crea ningún archivo de snapshot

### Requirement: Reanudación por TITN

El enriquecimiento MUST guardar el último `TITN` procesado y SHALL reanudar desde el siguiente pendiente tras un fallo.

#### Scenario: Reinicio del worker

- **WHEN** el worker se reinicia a mitad de un lote
- **THEN** el siguiente trabajo continúa desde el último `TITN` persistido
- **AND** no repite las fichas ya marcadas con `detail_fetched_at`

### Requirement: Errores y reintentos

Una ficha fallida MUST registrarse, reintentarse hasta el máximo configurado y SHALL excluirse del lote activo tras agotar los intentos.

#### Scenario: Ficha con error persistente

- **WHEN** una ficha falla tres veces
- **THEN** se marca con error y no bloquea el resto del lote
- **AND** queda visible para revisión manual

### Requirement: Actualización idempotente de ejemplares

Repetir el enriquecimiento de un TITN MUST actualizar sus ejemplares existentes por `external_key` sin duplicarlos.

#### Scenario: Reenriquecer una edición

- **WHEN** se procesa de nuevo un TITN ya enriquecido
- **THEN** se actualizan sus ejemplares y relaciones
- **AND** no se crean duplicados

### Requirement: Enriquecimiento de registros nuevos

El enriquecimiento programado MUST poder limitarse a las ediciones descubiertas desde un instante `since` y SHALL conservar el resto de pendientes para ejecuciones manuales.

#### Scenario: Solo nuevos

- **WHEN** un enriquecimiento recibe un `since`
- **THEN** selecciona solo ediciones con `discovery_seen_at` mayor o igual que `since` y sin `detail_fetched_at`
- **AND** no procesa stubs anteriores

#### Scenario: Enriquecimiento manual completo

- **WHEN** el operador lanza "Enriquecer pendientes" desde el dashboard
- **THEN** se seleccionan todos los stubs pendientes, sin filtro `since`
- **AND** se respeta el límite de lote configurado

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

### Requirement: Detección de captcha sin falsos positivos

El recolector MUST considerar que una respuesta contiene un captcha solo cuando incluye un desafío de reCAPTCHA real, como el script `g-recaptcha`, `grecaptcha` o el campo `g-recaptcha-response`. El texto de ayuda de AbsysNet que menciona `No soy un robot` SHALL NOT considerarse un captcha por sí solo.

#### Scenario: Listado con texto de ayuda

- **WHEN** el OPAC devuelve un listado de resultados con el texto de ayuda `Verifique que ha chequeado 'No soy un robot'` y sin desafío de reCAPTCHA
- **THEN** el recolector no incrementa el contador de captchas
- **AND** no lanza la detención por captcha
- **AND** el descubrimiento continúa con la siguiente página

#### Scenario: Página con desafío real

- **WHEN** la respuesta contiene `g-recaptcha`, `grecaptcha` o un campo `g-recaptcha-response`
- **THEN** el recolector la trata como una página de captcha
- **AND** incrementa el contador de captchas de la fuente
- **AND** aplica la política de FlareSolverr o la pausa configurada

#### Scenario: Ficha de detalle con texto de ayuda

- **WHEN** una ficha de detalle de Andalucía contiene el texto de ayuda pero no un desafío de reCAPTCHA
- **THEN** la ficha se parsea y se guarda sin lanzar la detención por captcha

#### Scenario: Respuesta resuelta por FlareSolverr

- **WHEN** FlareSolverr devuelve una página con el texto de ayuda y sin desafío de reCAPTCHA
- **THEN** el recolector considera el captcha resuelto
- **AND** no incrementa el contador de captchas fallidos

#### Scenario: Madrid sin captcha

- **WHEN** una página de Madrid no contiene un desafío de reCAPTCHA
- **THEN** el recolector no la marca como captcha
- **AND** el comportamiento de Madrid no cambia
