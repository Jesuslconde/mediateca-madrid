# dashboard-ingesta Specification

## Purpose

Ofrecer al operador una vista web pequeña y de solo lectura para conocer el estado de los trabajos de ingesta, la cobertura del catálogo y la salud del worker sin consultar PostgreSQL ni ejecutar comandos.

## Requirements

### Requirement: Vista web de solo lectura

El sistema MUST exponer una página web que muestre el estado de los trabajos de ingesta y la cobertura del catálogo, y MUST limitar las escrituras a la configuración, al encolado de trabajos y a la agrupación manual de obras.

#### Scenario: Acceso a la vista
- **WHEN** el operador abre la URL del dashboard
- **THEN** recibe una página HTML con el estado de los trabajos y la cobertura
- **AND** la carga no crea, modifica ni elimina trabajos, ediciones ni entradas del índice

#### Scenario: Refresco sin efectos secundarios
- **WHEN** el operador recarga la página varias veces
- **THEN** la vista vuelve a leer el estado actual
- **AND** no se ejecuta ninguna escritura salvo que el operador envíe un formulario de configuración, de encolado o de agrupación

#### Scenario: Escritura de configuración explícita
- **WHEN** el operador guarda la configuración de FlareSolverr, de TMDB o de la programación
- **THEN** solo se escribe esa configuración
- **AND** los trabajos, las ediciones y el índice permanecen intactos

#### Scenario: Encolado explícito de trabajos
- **WHEN** el operador pulsa una acción de tareas bajo demanda
- **THEN** se crea como máximo un trabajo `pending` del tipo solicitado
- **AND** no se ejecuta la ingesta dentro del proceso del dashboard

#### Scenario: Escritura de agrupación manual
- **WHEN** el operador guarda una agrupación manual desde el dashboard
- **THEN** solo se modifican la obra de las ediciones seleccionadas y las marcas de agrupación
- **AND** no se crean ni eliminan ediciones, ejemplares o trabajos

### Requirement: Configuración de FlareSolverr desde el dashboard

El dashboard MUST mostrar y permitir guardar la URL de FlareSolverr. La URL guardada SHALL prevalecer sobre `MEDIATECA_FLARESOLVERR_URL`; si no hay valor guardado, se usa la variable de entorno. El sistema MUST validar que sea una URL HTTP o HTTPS y SHALL rechazar valores inválidos sin cambiar la configuración vigente.

#### Scenario: Mostrar configuración vigente

- **WHEN** el operador abre el dashboard
- **THEN** ve la URL efectiva de FlareSolverr o un campo vacío si no está configurada
- **AND** ve si el origen es la configuración del dashboard, la variable de entorno o ninguno
- **AND** ve si la resolución de captchas está activa

#### Scenario: Guardar una URL válida

- **WHEN** el operador envía una URL HTTP o HTTPS válida
- **THEN** la configuración se persiste en PostgreSQL
- **AND** los trabajos de ingesta lanzados después usan esa URL
- **AND** el dashboard muestra el nuevo valor y su origen

#### Scenario: Limpiar la configuración

- **WHEN** el operador guarda el campo vacío
- **THEN** se elimina la URL persistida
- **AND** se usa la variable de entorno si existe
- **AND** si tampoco existe, la resolución de captchas queda desactivada

#### Scenario: URL inválida

- **WHEN** el operador envía un valor que no es una URL HTTP o HTTPS
- **THEN** el dashboard muestra un error comprensible
- **AND** no se modifica la configuración vigente

#### Scenario: Error al persistir

- **WHEN** la base de datos no permite guardar la configuración
- **THEN** el dashboard muestra un error comprensible
- **AND** no deja la configuración a medio actualizar

### Requirement: Configuración del token de TMDB desde el dashboard

El dashboard MUST mostrar y permitir guardar o borrar el token de API de TMDB. El token guardado SHALL persistirse en `app_config` y prevalecer sobre `MEDIATECA_TMDB_API_TOKEN`; si no hay valor guardado, se usa la variable de entorno. El sistema MUST validar el token y SHALL rechazar valores inválidos sin cambiar la configuración vigente.

#### Scenario: Mostrar configuración vigente

- **WHEN** el operador abre el dashboard
- **THEN** ve si hay token de TMDB configurado y su origen (`dashboard`, `entorno` o `ninguno`)
- **AND** ve solo una versión enmascarada del token, nunca el valor completo
- **AND** ve si el enriquecimiento TMDB está activo o inactivo

#### Scenario: Guardar un token válido

- **WHEN** el operador envía un token válido
- **THEN** el token se persiste en `app_config`
- **AND** los trabajos de enriquecimiento y backfill lanzados después lo usan
- **AND** el dashboard muestra el nuevo origen y la versión enmascarada

#### Scenario: Campo vacío conserva el token

- **WHEN** el operador guarda el formulario con el campo vacío y sin marcar la opción de borrado
- **THEN** se conserva el token guardado
- **AND** no se usa la variable de entorno mientras exista ese token

#### Scenario: Borrar el token

- **WHEN** el operador marca la opción de borrado y guarda
- **THEN** se elimina el token persistido
- **AND** se usa la variable de entorno si existe
- **AND** si tampoco existe, el enriquecimiento TMDB queda desactivado

#### Scenario: Token inválido

- **WHEN** el operador envía un valor con espacios, caracteres de control o una longitud fuera del rango admitido
- **THEN** el dashboard muestra un error comprensible
- **AND** no se modifica la configuración vigente

#### Scenario: Error al persistir

- **WHEN** la base de datos no permite guardar la configuración
- **THEN** el dashboard muestra un error comprensible
- **AND** no deja la configuración a medio actualizar

### Requirement: Protección del token de TMDB

El sistema MUST NOT mostrar el token completo en la interfaz ni registrarlo en logs o mensajes de error. Las acciones de escritura del token SHALL requerir el token de administración cuando `MEDIATECA_DASHBOARD_ADMIN_TOKEN` esté configurado.

#### Scenario: Token no expuesto en la vista

- **WHEN** el dashboard muestra la configuración de TMDB
- **THEN** el HTML no contiene el token completo
- **AND** solo muestra un identificador enmascarado

#### Scenario: Token no registrado en logs

- **WHEN** se guarda, valida o usa el token
- **THEN** los logs no incluyen el valor del token
- **AND** los errores tampoco lo incluyen

#### Scenario: Escritura sin administración

- **WHEN** un operador sin token de administración intenta guardar o borrar el token de TMDB
- **THEN** la escritura se rechaza con un mensaje comprensible
- **AND** no se modifica la base de datos

### Requirement: Resumen de trabajos por estado y tipo

El sistema MUST mostrar el número de trabajos agrupados por estado (`pending`, `running`, `completed`, `failed`, `cancelled`) y por tipo (`discover`, `enrich`, `index`, `tmdb`).

#### Scenario: Conteo por estado

- **WHEN** existen trabajos en varios estados
- **THEN** la vista muestra el total de cada estado
- **AND** los estados sin trabajos se muestran con valor cero

#### Scenario: Conteo por tipo

- **WHEN** existen trabajos de descubrimiento, enriquecimiento, indexación y actualización TMDB
- **THEN** la vista muestra el total de cada tipo
- **AND** los tipos sin trabajos se muestran con valor cero

### Requirement: Detalle de trabajos recientes

El sistema MUST listar los trabajos más recientes ordenados por fecha de creación descendente, con identificador, tipo, estado, cursor, intentos, fechas de inicio y fin, heartbeat y error.

#### Scenario: Trabajo fallido visible

- **WHEN** un trabajo termina en estado `failed`
- **THEN** la vista muestra su error y el número de intentos realizados
- **AND** el trabajo aparece entre los más recientes

#### Scenario: Límite de trabajos mostrados

- **WHEN** hay más trabajos que el límite configurado
- **THEN** la vista muestra solo los más recientes
- **AND** el resumen por estado sigue contando todos los trabajos

### Requirement: Cobertura del catálogo

El sistema SHALL mostrar el número de ediciones descubiertas, enriquecidas, pendientes y fallidas, junto con el porcentaje de enriquecimiento sobre el total y el desglose por fuente.

#### Scenario: Cobertura parcial

- **WHEN** se han enriquecido parte de las ediciones del catálogo
- **THEN** la vista muestra los conteos y el porcentaje de enriquecimiento
- **AND** el número de pendientes coincide con las ediciones sin enriquecer
- **AND** cada fuente habilitada muestra su propio desglose

#### Scenario: Catálogo vacío

- **WHEN** no existen ediciones
- **THEN** la vista muestra cero en todas las métricas
- **AND** el porcentaje de enriquecimiento se muestra como cero sin dividir por cero

### Requirement: Salud del worker

El sistema MUST mostrar el último heartbeat del worker y SHALL marcar el estado como `degraded` cuando el heartbeat supere el umbral configurado.

#### Scenario: Worker activo

- **WHEN** el heartbeat es reciente
- **THEN** la vista muestra el estado del worker como `ok`
- **AND** muestra la fecha del último heartbeat

#### Scenario: Worker detenido

- **WHEN** el heartbeat supera el umbral configurado o no existe
- **THEN** la vista muestra el estado del worker como `degraded`
- **AND** el resto de métricas y trabajos sigue visible

### Requirement: Endpoint de datos dinámicos del dashboard

El dashboard MUST exponer endpoints de solo lectura que devuelven en formato JSON los datos dinámicos de Inicio y de Tareas. Estos endpoints SHALL devolver la misma información que muestran las páginas y SHALL NOT crear, modificar ni eliminar datos.

#### Scenario: Datos de Inicio

- **WHEN** se consulta el endpoint de datos de Inicio
- **THEN** devuelve la salud del worker, el resumen de trabajos por estado, tipo y fuente, la cobertura del catálogo y las métricas de ingesta
- **AND** no modifica trabajos, ediciones ni configuración

#### Scenario: Datos de Tareas

- **WHEN** se consulta el endpoint de datos de Tareas
- **THEN** devuelve los trabajos recientes y el estado activo de cada tipo de trabajo
- **AND** no modifica trabajos, ediciones ni configuración

#### Scenario: Base de datos no disponible

- **WHEN** la base de datos no responde al consultar un endpoint de datos dinámicos
- **THEN** el endpoint devuelve un estado de error o degradado comprensible
- **AND** no expone trazas internas ni detalles de conexión

### Requirement: Actualización automática

El sistema SHALL refrescar automáticamente los datos dinámicos de las páginas de Inicio y Tareas con un intervalo configurable, obteniendo únicamente la información que cambia mediante una llamada AJAX a un endpoint, sin recargar la página completa ni requerir que el operador la recargue manualmente. La página de Configuración SHALL NOT refrescarse automáticamente para no perder cambios en los formularios.

#### Scenario: Refresco periódico

- **WHEN** transcurre el intervalo de refresco configurado
- **THEN** la vista actualiza los datos mostrados en Inicio y Tareas mediante una llamada AJAX, sin recargar la página completa
- **AND** el intervalo puede cambiarse mediante configuración de entorno

#### Scenario: Refresco parcial de Tareas

- **WHEN** transcurre el intervalo de refresco configurado en la página de Tareas
- **THEN** la página actualiza la tabla de trabajos recientes y el estado activo de las tareas sin recargar la página completa
- **AND** los valores introducidos en los formularios de acciones bajo demanda no se pierden con el refresco

#### Scenario: Configuración sin refresco

- **WHEN** el operador está editando un formulario en Configuración
- **THEN** la página no se refresca automáticamente
- **AND** los valores introducidos no se pierden por el refresco

#### Scenario: Fallo en la actualización parcial

- **WHEN** la base de datos no responde durante una actualización parcial
- **THEN** la página muestra un estado degradado comprensible sin recargarse
- **AND** no expone trazas internas ni detalles de conexión

### Requirement: Tolerancia a fallos de la base de datos

El sistema MUST responder con un estado de error comprensible cuando la base de datos no está disponible, sin exponer trazas internas ni caerse.

#### Scenario: Base de datos no disponible

- **WHEN** la base de datos no responde
- **THEN** la vista devuelve un estado `degraded` con un mensaje comprensible
- **AND** no muestra trazas de pila ni detalles de conexión

### Requirement: Tareas bajo demanda

El dashboard MUST permitir encolar descubrimiento incremental, descubrimiento completo, enriquecimiento, indexación, actualización de metadatos TMDB y recarga de direcciones de bibliotecas, y SHALL rechazar la acción si ya existe un trabajo activo del mismo tipo. La actualización TMDB SHALL permitir elegir el lote y reactualizar también las ediciones ya sincronizadas, y MUST rechazarse si no hay token de TMDB configurado. La recarga de bibliotecas SHALL procesar solo bibliotecas ya conocidas, actualizando sus direcciones y creando o actualizando sus sucursales sin crear bibliotecas nuevas.

#### Scenario: Buscar novedades

- **WHEN** el operador pulsa "Buscar novedades"
- **THEN** se encola un `discover` incremental con el cursor del último descubrimiento completado
- **AND** el worker lo procesa cuando esté libre

#### Scenario: Enriquecer pendientes

- **WHEN** el operador pulsa "Enriquecer pendientes"
- **THEN** se encola un `enrich` con el lote indicado
- **AND** se procesan todos los stubs pendientes, no solo los de la última búsqueda

#### Scenario: Actualizar metadatos TMDB

- **WHEN** el operador pulsa "Actualizar metadatos TMDB" con un lote y, opcionalmente, la casilla de refresco
- **THEN** se encola un trabajo `tmdb` con el lote y el modo indicados
- **AND** el trabajo se ejecuta en el worker y queda registrado en el historial

#### Scenario: Recargar direcciones de bibliotecas

- **WHEN** el operador pulsa "Recargar direcciones de bibliotecas"
- **THEN** se encola un trabajo `branches`
- **AND** el trabajo procesa solo bibliotecas ya conocidas y crea o actualiza sus sucursales
- **AND** las fichas de bibliotecas desconocidas se omiten sin crear bibliotecas nuevas

#### Scenario: Actualización TMDB sin token

- **WHEN** el operador solicita una actualización TMDB sin un token configurado
- **THEN** el dashboard muestra un error comprensible
- **AND** no se crea ningún trabajo

#### Scenario: Trabajo duplicado

- **WHEN** ya hay un trabajo `pending` o `running` del mismo tipo
- **THEN** el dashboard muestra un error comprensible
- **AND** no crea otro trabajo

### Requirement: Programación configurable

El dashboard MUST mostrar y permitir guardar la activación, los intervalos de descubrimiento, barrido completo y enriquecimiento, y el tamaño de lote. La configuración SHALL persistirse en `app_config` y ser usada por el scheduler sin reiniciar.

#### Scenario: Mostrar programación

- **WHEN** el operador abre el dashboard
- **THEN** ve el estado de la programación, la última y la próxima ejecución
- **AND** ve los trabajos activos por tipo y los pendientes de enriquecer

#### Scenario: Guardar intervalos válidos

- **WHEN** el operador guarda intervalos y lote válidos
- **THEN** la configuración se persiste y el scheduler la aplica en la siguiente comprobación
- **AND** el dashboard muestra los nuevos valores

#### Scenario: Valor inválido

- **WHEN** el operador envía un intervalo o lote fuera de rango
- **THEN** el dashboard muestra un error
- **AND** no modifica la configuración vigente

### Requirement: Token de escritura del dashboard

El sistema MUST exigir un token para las acciones de escritura del dashboard cuando `MEDIATECA_DASHBOARD_ADMIN_TOKEN` esté configurado, y SHALL permitir la lectura sin token.

#### Scenario: Escritura sin token

- **WHEN** un operador intenta guardar configuración o encolar un trabajo sin token válido
- **THEN** la escritura se rechaza con un mensaje comprensible
- **AND** no se modifica la base de datos

#### Scenario: Login correcto

- **WHEN** el operador introduce el token correcto
- **THEN** se guarda una cookie de administración `HttpOnly` y `SameSite=Strict`
- **AND** puede usar los formularios de escritura durante la sesión

### Requirement: Menú lateral de navegación

El dashboard MUST mostrar un menú lateral persistente en las páginas de Inicio, Catálogo, Agrupación, Tareas y Configuración, con enlaces a `/`, `/catalogo`, `/agrupacion`, `/tareas` y `/configuracion`, la sección activa resaltada y acceso al estado de administración, login y logout.

#### Scenario: Navegación entre páginas
- **WHEN** el operador pulsa una opción del menú lateral
- **THEN** se abre la página correspondiente sin recargar la aplicación completa
- **AND** el menú sigue visible en la nueva página

#### Scenario: Sección activa
- **WHEN** el operador está en una de las cinco páginas
- **THEN** el menú resalta la opción de esa página
- **AND** las demás opciones siguen disponibles

#### Scenario: Administración desde el menú
- **WHEN** el operador necesita iniciar o cerrar sesión de administración
- **THEN** dispone de esas acciones en el menú lateral desde cualquier página
- **AND** el estado de la sesión se muestra en el menú

#### Scenario: Acceso a la agrupación
- **WHEN** el operador pulsa la opción Agrupación
- **THEN** se abre `/agrupacion`
- **AND** la opción aparece resaltada como sección activa

### Requirement: Página de Inicio centrada en estados

La página de Inicio MUST mostrar únicamente la salud del worker, el resumen de trabajos por estado y tipo, la cobertura del catálogo y las métricas de ingesta. SHALL NOT incluir la tabla de trabajos recientes, las acciones de encolado ni los formularios de configuración.

#### Scenario: Inicio sin administración

- **WHEN** el operador abre `/`
- **THEN** ve los estados, la cobertura y las métricas
- **AND** no ve la tabla de trabajos recientes, los botones de encolado ni los formularios de configuración

#### Scenario: Acceso a las demás páginas

- **WHEN** el operador necesita ver trabajos o cambiar configuración
- **THEN** el menú lateral le ofrece Tareas y Configuración
- **AND** Inicio no duplica esas secciones

### Requirement: Página de Tareas

La página de Tareas MUST mostrar los trabajos recientes y las acciones de descubrimiento, enriquecimiento, indexación, actualización de metadatos TMDB y recarga de direcciones de bibliotecas. SHALL conservar las reglas de encolado, la desactivación de acciones con un trabajo activo y la protección de escritura. SHALL mostrar la concurrencia efectiva del worker y explicar las reglas de exclusión por tipo y dependencia.

#### Scenario: Visualización de trabajos

- **WHEN** el operador abre `/tareas`
- **THEN** ve la tabla de trabajos recientes con los mismos campos y orden que antes
- **AND** ve el estado activo de cada tipo de trabajo

#### Scenario: Acciones bajo demanda

- **WHEN** el operador pulsa una acción de descubrimiento, enriquecimiento, indexación, actualización TMDB o recarga de bibliotecas
- **THEN** se encola el trabajo con las mismas reglas que en la vista anterior
- **AND** las acciones con un trabajo activo del mismo tipo siguen deshabilitadas

#### Scenario: Acción incompatible con otra activa

- **WHEN** el operador encola un trabajo incompatible con otro que está en ejecución
- **THEN** el trabajo queda `pending`
- **AND** se ejecuta cuando termina el que lo bloquea

#### Scenario: Redirección con mensaje

- **WHEN** una acción de tareas termina con éxito o error
- **THEN** el operador vuelve a `/tareas`
- **AND** ve el mensaje correspondiente en esa página

#### Scenario: Escritura sin administración

- **WHEN** el operador no tiene sesión de administración y hay token configurado
- **THEN** las acciones de encolado aparecen deshabilitadas o se rechazan
- **AND** no se crea ningún trabajo

### Requirement: Página de Configuración

La página de Configuración MUST agrupar la programación, la concurrencia del worker, la configuración de FlareSolverr y la configuración del token de TMDB. Cada sección SHALL conservar su contrato vigente de validación, precedencia, máscara y protección de escritura. La concurrencia SHALL validarse entre 1 y 5 y guardarse en `app_config` con precedencia sobre el entorno.

#### Scenario: Secciones de configuración

- **WHEN** el operador abre `/configuracion`
- **THEN** ve la programación, la concurrencia efectiva del worker, la URL efectiva de FlareSolverr y el estado del token de TMDB
- **AND** ve los formularios correspondientes si tiene acceso de administración

#### Scenario: Configurar la concurrencia

- **WHEN** el operador guarda una concurrencia de 3
- **THEN** el valor queda en `app_config`
- **AND** el dashboard indica que el worker debe reiniciarse para aplicarlo

#### Scenario: Concurrencia fuera de rango

- **WHEN** el operador guarda un valor menor que 1 o mayor que 5
- **THEN** no se modifica la configuración
- **AND** ve un mensaje de error comprensible

#### Scenario: Guardado y mensajes

- **WHEN** el operador guarda una sección con éxito o error
- **THEN** vuelve a `/configuracion`
- **AND** ve el mensaje correspondiente en esa página

#### Scenario: Contratos conservados

- **WHEN** el operador guarda o borra la configuración de FlareSolverr, TMDB o la programación
- **THEN** se aplican las mismas reglas de validación, precedencia y protección que antes del cambio
- **AND** los trabajos, las ediciones y el índice permanecen intactos

### Requirement: Página de Catálogo

El dashboard MUST exponer una página `/catalogo` de consulta con un resumen de ediciones por estado de enriquecimiento OPAC y TMDB y una tabla paginada. La página SHALL NOT crear ni eliminar ediciones; su única escritura SHALL ser la asignación manual de TMDB, protegida por el token de administración cuando esté configurado.

#### Scenario: Acceso a la página

- **WHEN** el operador abre `/catalogo`
- **THEN** recibe una página HTML con el resumen por estado y la tabla de ediciones
- **AND** la carga no modifica ediciones, trabajos ni configuración

#### Scenario: Catálogo vacío

- **WHEN** no existen ediciones
- **THEN** el resumen muestra cero en todos los estados
- **AND** la tabla indica que no hay resultados sin dividir por cero

#### Scenario: Asignación manual de TMDB

- **WHEN** una edición está en estado TMDB `unmatched`
- **THEN** la fila ofrece un campo para introducir un ID de TMDB y confirmarlo
- **AND** la acción solo está disponible con administración desbloqueada y token de TMDB configurado
- **AND** al confirmar un ID válido la edición pasa a `matched` y vuelve a la misma página con sus filtros

#### Scenario: Base de datos no disponible

- **WHEN** la base de datos no responde
- **THEN** la página muestra un estado degradado comprensible
- **AND** no expone trazas internas ni detalles de conexión

### Requirement: Resumen de estado de enriquecimiento

El sistema SHALL mostrar, para el conjunto filtrado, el total de ediciones y su reparto por estado OPAC (`pending`, `enriched`, `failed`) y por estado TMDB (`pending`, `matched`, `unmatched`, `error`, `skipped`), además de las desaparecidas.

#### Scenario: Reparto por estado

- **WHEN** el operador abre la página sin filtros
- **THEN** ve el total de ediciones y el número de cada estado OPAC y TMDB
- **AND** los estados sin ediciones se muestran con valor cero

#### Scenario: Resumen filtrado

- **WHEN** el operador aplica un filtro
- **THEN** el resumen se recalcula sobre las ediciones que cumplen el filtro
- **AND** el total de coincidencias coincide con el de la tabla

### Requirement: Filtros del catálogo

El sistema MUST permitir filtrar las ediciones por estado OPAC, estado TMDB, desaparición, texto libre, soporte, biblioteca, año, idioma y país, y SHALL combinar los filtros activos y paginar los resultados.

#### Scenario: Filtrar pendientes OPAC

- **WHEN** el operador filtra por estado OPAC `pending`
- **THEN** la tabla solo muestra ediciones sin ficha OPAC
- **AND** el resumen refleja ese subconjunto

#### Scenario: Filtrar resultados TMDB sin coincidencia

- **WHEN** el operador filtra por estado TMDB `unmatched`
- **THEN** la tabla solo muestra ediciones emparejadas sin coincidencia
- **AND** no incluye las que aún no se han intentado

#### Scenario: Combinar filtros

- **WHEN** el operador combina texto, soporte, biblioteca y año
- **THEN** la tabla solo muestra ediciones que cumplen todos los filtros
- **AND** los filtros vacíos no restringen el resultado

#### Scenario: Sin resultados

- **WHEN** ningún registro cumple los filtros
- **THEN** la tabla indica que no hay resultados
- **AND** el operador puede limpiar los filtros

#### Scenario: Paginación

- **WHEN** hay más resultados que el tamaño de página
- **THEN** la página muestra solo el tramo solicitado
- **AND** el total de coincidencias sigue visible

### Requirement: Columnas de la tabla del catálogo

La tabla SHALL mostrar, por edición, `TITN`, título, año, soporte principal, estado e intentos OPAC, último error OPAC, estado e intentos TMDB, último error TMDB, fechas de descubrimiento, ficha y TMDB, la marca de desaparición y, cuando el estado TMDB sea `unmatched`, el control de asignación manual de un ID de TMDB.

#### Scenario: Edición pendiente

- **WHEN** una edición no se ha intentado enriquecer
- **THEN** la fila muestra estado OPAC `pending`, intentos `0` y sin error

#### Scenario: Edición con fallo OPAC

- **WHEN** una edición falló tras los reintentos
- **THEN** la fila muestra estado OPAC `failed`, el número de intentos y el último error

#### Scenario: Edición desaparecida

- **WHEN** una edición tiene `missing_at`
- **THEN** la fila muestra la marca de desaparición y su fecha
- **AND** el estado de enriquecimiento se sigue mostrando

### Requirement: Fuente en la operación del dashboard

El dashboard MUST identificar la fuente en la cobertura, en la tabla de catálogo y en los trabajos recientes. Las acciones de encolado SHALL indicar la fuente sobre la que operan y SHALL rechazar un duplicado solo cuando coincidan tipo y fuente. Las fuentes deshabilitadas SHALL mostrarse como tales y SHALL NOT ofrecer acciones de ingesta.

#### Scenario: Cobertura por fuente

- **WHEN** el operador abre la página de Inicio con varias fuentes
- **THEN** ve el total del catálogo y el desglose de cada fuente
- **AND** las fuentes deshabilitadas aparecen identificadas

#### Scenario: Encolar una tarea con fuente

- **WHEN** el operador pulsa una acción de descubrimiento o enriquecimiento
- **THEN** el trabajo se crea para la fuente seleccionada
- **AND** el mensaje de confirmación identifica esa fuente

#### Scenario: Catálogo con fuente

- **WHEN** el operador consulta la tabla de catálogo
- **THEN** cada fila muestra la fuente de la edición
- **AND** puede filtrar por fuente

#### Scenario: Fuente deshabilitada

- **WHEN** una fuente está deshabilitada
- **THEN** sus acciones de ingesta no están disponibles
- **AND** sus datos siguen visibles en la cobertura y en el catálogo

### Requirement: Página de Agrupación

El dashboard MUST exponer una página `/agrupacion` para consultar ediciones y corregir manualmente su obra. La página SHALL permitir agrupar varias ediciones en una obra existente o nueva, y SHALL permitir devolver una edición al comportamiento automático. La obra destino MUST buscarse por texto reutilizando el filtro `q`, mostrando solo las coincidencias.

#### Scenario: Consulta de ediciones
- **WHEN** el operador abre `/agrupacion`
- **THEN** ve una tabla paginada de ediciones con título, año, soporte, fuente, TITN, obra actual y marca manual
- **AND** puede filtrar por texto (`q`), fuente, soporte y estado de agrupación
- **AND** la carga no modifica datos

#### Scenario: Búsqueda de la obra destino
- **WHEN** el operador escribe texto en el filtro `q`
- **THEN** el formulario muestra únicamente las obras cuyo título uniforme o año coincide con ese texto, hasta un máximo de 20
- **AND** no se ofrece un desplegable con la totalidad de las obras
- **AND** si `q` está vacío, no se listan obras candidatas

#### Scenario: Agrupar en una obra existente
- **WHEN** el operador selecciona varias ediciones, elige una obra destino de las coincidencias de texto y confirma
- **THEN** las ediciones seleccionadas pasan a esa obra
- **AND** todas las ediciones de la obra destino quedan marcadas como manuales
- **AND** las obras antiguas que quedan sin ediciones se eliminan
- **AND** las ediciones afectadas se reindexan

#### Scenario: Agrupar en una obra nueva
- **WHEN** el operador selecciona varias ediciones e introduce título uniforme y año
- **THEN** se reutiliza la obra con esa clave si ya existe
- **AND** en caso contrario se crea una obra manual
- **AND** las ediciones seleccionadas pasan a esa obra

#### Scenario: Volver a automático
- **WHEN** el operador desvincula ediciones seleccionadas
- **THEN** se limpia su marca manual
- **AND** cada edición vuelve a la agrupación automática por título uniforme y año

#### Scenario: Protección de escritura
- **WHEN** el operador no tiene token de administración y hay uno configurado
- **THEN** las acciones de agrupación se rechazan con un mensaje comprensible
- **AND** no se modifica ninguna edición ni obra

#### Scenario: Base de datos no disponible
- **WHEN** la base de datos no responde al abrir `/agrupacion`
- **THEN** la página muestra un estado degradado comprensible
- **AND** no expone trazas internas ni detalles de conexión
