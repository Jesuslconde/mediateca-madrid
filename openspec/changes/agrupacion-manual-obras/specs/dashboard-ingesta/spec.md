# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Página de Agrupación

El dashboard MUST exponer una página `/agrupacion` para consultar ediciones y corregir manualmente su obra. La página SHALL permitir agrupar varias ediciones en una obra existente o nueva, y SHALL permitir devolver una edición al comportamiento automático.

#### Scenario: Consulta de ediciones
- **WHEN** el operador abre `/agrupacion`
- **THEN** ve una tabla paginada de ediciones con título, año, soporte, fuente, TITN, obra actual y marca manual
- **AND** puede filtrar por texto, fuente, soporte y estado de agrupación
- **AND** la carga no modifica datos

#### Scenario: Agrupar en una obra existente
- **WHEN** el operador selecciona varias ediciones, elige una obra destino y confirma
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
