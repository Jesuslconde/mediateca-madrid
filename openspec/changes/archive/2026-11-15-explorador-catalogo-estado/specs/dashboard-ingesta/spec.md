# Spec Delta

## MODIFIED Requirements

### Requirement: Menú lateral de navegación

El dashboard MUST mostrar un menú lateral persistente en las páginas de Inicio, Catálogo, Tareas y Configuración, con enlaces a `/`, `/catalogo`, `/tareas` y `/configuracion`, la sección activa resaltada y acceso al estado de administración, login y logout.

#### Scenario: Navegación entre páginas

- **WHEN** el operador pulsa una opción del menú lateral
- **THEN** se abre la página correspondiente sin recargar la aplicación completa
- **AND** el menú sigue visible en la nueva página

#### Scenario: Sección activa

- **WHEN** el operador está en una de las cuatro páginas
- **THEN** el menú resalta la opción de esa página
- **AND** las demás opciones siguen disponibles

#### Scenario: Administración desde el menú

- **WHEN** el operador necesita iniciar o cerrar sesión de administración
- **THEN** dispone de esas acciones en el menú lateral desde cualquier página
- **AND** el estado de la sesión se muestra en el menú

## ADDED Requirements

### Requirement: Página de Catálogo

El dashboard MUST exponer una página `/catalogo` de solo lectura con un resumen de ediciones por estado de enriquecimiento OPAC y TMDB y una tabla paginada de ediciones. La página SHALL NOT crear, modificar ni eliminar datos.

#### Scenario: Acceso a la página

- **WHEN** el operador abre `/catalogo`
- **THEN** recibe una página HTML con el resumen por estado y la tabla de ediciones
- **AND** la carga no modifica ediciones, trabajos ni configuración

#### Scenario: Catálogo vacío

- **WHEN** no existen ediciones
- **THEN** el resumen muestra cero en todos los estados
- **AND** la tabla indica que no hay resultados sin dividir por cero

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

La tabla SHALL mostrar, por edición, `TITN`, título, año, soporte principal, estado e intentos OPAC, último error OPAC, estado e intentos TMDB, último error TMDB, fechas de descubrimiento, ficha y TMDB, y la marca de desaparición.

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
