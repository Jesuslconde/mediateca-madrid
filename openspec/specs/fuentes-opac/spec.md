# fuentes-opac Specification

## Purpose
Definir las fuentes OPAC disponibles, su perfil de recolección y la identidad global de las ediciones para que el catálogo pueda incorporar nuevas redes sin colisiones entre catálogos.

## Requirements

### Requirement: Registro de fuentes OPAC

El sistema MUST mantener un registro persistente de fuentes con un código estable, nombre visible, perfil de recolección y estado operativo. Cada fuente SHALL declarar su URL base, ruta del OPAC, patrón de sesión, filtro de formato, tipo de adaptador, retardo y política de captcha. El código SHALL ser único y no SHALL cambiar cuando cambie el nombre visible.

#### Scenario: Fuente Madrid existente

- **WHEN** se inicializa una base con el catálogo actual
- **THEN** existe la fuente `madrid` con su perfil y estado habilitado
- **AND** las ediciones existentes quedan asociadas a ella

#### Scenario: Alta de fuente

- **WHEN** se registra una fuente nueva con código único y perfil válido
- **THEN** queda disponible para la ingesta
- **AND** no se activa hasta que se habilite explícitamente

#### Scenario: Código duplicado

- **WHEN** se intenta registrar dos fuentes con el mismo código
- **THEN** se rechaza el alta
- **AND** no se modifica el registro existente

### Requirement: Identidad global de edición

Cada edición MUST identificarse por `record_id`, compuesto por el código de fuente y el `TITN` original (`<fuente>:<titn>`). La pareja `(fuente, titn)` SHALL ser única y el mismo `TITN` SHALL poder existir en fuentes distintas. `record_id` SHALL ser estable y SHALL NOT cambiar al reenriquecer la edición.

#### Scenario: Mismo TITN en dos fuentes

- **WHEN** Madrid y otra fuente tienen un registro con el mismo `TITN`
- **THEN** existen dos ediciones con `record_id` distintos
- **AND** cada una conserva sus metadatos y ejemplares

#### Scenario: Compatibilidad con TITN suelto

- **WHEN** un cliente solicita un identificador sin prefijo de fuente
- **THEN** se resuelve como `madrid:<identificador>`
- **AND** la respuesta indica la fuente resuelta

#### Scenario: Identificador inválido

- **WHEN** el identificador no tiene un formato válido o la fuente no existe
- **THEN** la petición se rechaza con un error legible
- **AND** no se crea ni modifica ninguna edición

### Requirement: Contrato de adaptador OPAC

Cada fuente MUST resolverse mediante el adaptador declarado en su perfil, que abra sesión cuando aplique, ejecute la búsqueda según el modo de descubrimiento de la fuente, recupere fichas y construya la URL permanente. El adaptador SHALL recibir el perfil de la fuente y SHALL NOT compartir sesión, cookies ni contadores de captcha con otra fuente. Una fuente de cobertura SHALL poder devolver metadatos y URL permanente sin ejemplares.

#### Scenario: Reutilización de AbsysNet

- **WHEN** dos fuentes usan AbsysNet con rutas y filtros distintos
- **THEN** ambas usan el mismo tipo de adaptador con perfiles diferentes
- **AND** cada una mantiene su propia sesión

#### Scenario: Aislamiento de sesión

- **WHEN** una fuente renueva su sesión o resuelve un captcha
- **THEN** la sesión de otra fuente no cambia
- **AND** sus contadores se mantienen separados

#### Scenario: URL permanente por fuente

- **WHEN** se serializa un registro
- **THEN** la URL del OPAC se construye con el perfil de su fuente
- **AND** no con una URL global

#### Scenario: Adaptador de cobertura

- **WHEN** una fuente declara cobertura
- **THEN** el adaptador devuelve metadatos y la URL permanente del registro
- **AND** no exige ejemplares ni comparte sesión con las fuentes AbsysNet

### Requirement: Aislamiento de fallos por fuente

Un fallo, captcha o fuente deshabilitada MUST NOT impedir la recolección o el enriquecimiento de las demás fuentes. El sistema SHALL registrar el fallo con la fuente afectada y SHALL mantener el estado de las otras fuentes.

#### Scenario: Captcha en una fuente

- **WHEN** una fuente devuelve un captcha que no se puede resolver
- **THEN** esa fuente detiene su trabajo
- **AND** las demás fuentes siguen operando

#### Scenario: Fuente deshabilitada

- **WHEN** una fuente está deshabilitada
- **THEN** el scheduler no encola trabajos para ella
- **AND** el catálogo y el índice conservan sus datos existentes

### Requirement: Fuente Andalucía operativa

El sistema SHALL registrar la fuente `andalucia` con perfil AbsysNet, estado habilitado y filtro de formato `Videograbaciones` (`select03=05`). La fuente SHALL poder ejecutar descubrimiento, enriquecimiento e indexado sin compartir sesión ni contadores con Madrid.

#### Scenario: Semilla de Andalucía

- **WHEN** se aplica la migración de la fuente sobre una base que ya contiene Madrid
- **THEN** existe la fuente `andalucia` habilitada con su perfil OPAC
- **AND** la fuente y el catálogo de Madrid no se modifican

#### Scenario: Reejecución de la semilla

- **WHEN** la migración de Andalucía se ejecuta por segunda vez
- **THEN** no se crea una fuente duplicada
- **AND** no se altera el perfil existente

#### Scenario: Tareas de Andalucía

- **WHEN** el scheduler evalúa las fuentes habilitadas
- **THEN** puede encolar trabajos para `andalucia`
- **AND** los trabajos de Madrid conservan su propia fuente y su propio cursor

#### Scenario: Misma TITN en dos fuentes

- **WHEN** Madrid y Andalucía tienen una edición con la misma `TITN`
- **THEN** existen dos ediciones con `record_id` distintos
- **AND** cada una conserva su fuente y sus propios ejemplares

#### Scenario: Ejecución desde la CLI

- **WHEN** el operador ejecuta `discover --fuente andalucia`
- **THEN** la recolección usa el perfil de Andalucía
- **AND** no reutiliza la sesión ni el filtro de Madrid

### Requirement: Fuentes autonómicas AbsysNet operativas

El sistema SHALL registrar con `adapter=absysnet` las fuentes `aragon`, `asturias`, `cantabria`, `castilla-leon`, `extremadura`, `la-rioja`, `murcia`, `navarra`, `pais-vasco` y `valencia`, cada una con `base_url`, `opac_path`, `session_pattern` y filtro de formato de vídeo calibrados. Cada fuente SHALL habilitarse tras su calibración. Ninguna SHALL compartir sesión, cookies, contadores ni cursores con otra.

#### Scenario: Semilla de las diez fuentes

- **WHEN** se aplica la migración de fuentes autonómicas sobre una base con Madrid y Andalucía
- **THEN** existen las diez fuentes registradas con su perfil AbsysNet
- **AND** las fuentes y el catálogo de Madrid y Andalucía no se modifican

#### Scenario: Reejecución de la semilla

- **WHEN** la migración se ejecuta por segunda vez
- **THEN** no se crea ninguna fuente duplicada
- **AND** no se altera el perfil existente

#### Scenario: Filtro de formato por fuente

- **WHEN** una fuente declara un código de vídeo distinto del de Madrid (`6`) o Andalucía (`05`)
- **THEN** su búsqueda usa el código de esa fuente
- **AND** no reutiliza el de otra fuente

#### Scenario: Aislamiento entre redes AbsysNet

- **WHEN** una de las diez fuentes falla o recibe un captcha
- **THEN** esa fuente detiene su trabajo
- **AND** las demás fuentes siguen operando con su propia sesión y su propio cursor

### Requirement: Fuentes de cobertura CCBIP operativas

El sistema SHALL registrar con `adapter=absysnet`, `options.discovery="novedades"` y `options.coverage=true` las fuentes `castilla-la-mancha`, `galicia`, `cataluna`, `baleares` y `canarias`, acotadas por su `subcat` del CCBIP (`BPCLM`, `BPGAL`, `BPCAT`, `BPEMAO_A`, `BPCANA`) y con `select03=06`. Cada fuente SHALL habilitarse tras validar su acotación y SHALL aportar metadatos y URL permanente sin ejemplares.

#### Scenario: Semilla de cobertura

- **WHEN** se aplica la migración de cobertura sobre una base con las diez fuentes AbsysNet
- **THEN** existen las cinco fuentes registradas con su `subcat`, su modo de descubrimiento y su modo cobertura
- **AND** las fuentes AbsysNet y su catálogo no se modifican

#### Scenario: Reejecución de la semilla de cobertura

- **WHEN** la migración de cobertura se ejecuta por segunda vez
- **THEN** no se crea ninguna fuente duplicada
- **AND** no se altera el perfil existente

#### Scenario: Acotación por comunidad

- **WHEN** se descubre la fuente `cataluna`
- **THEN** la búsqueda se acota al catálogo `BPCAT` del CCBIP
- **AND** no se ingestan registros de otras comunidades en esa fuente

#### Scenario: Edición sin ejemplares

- **WHEN** una fuente de cobertura devuelve un registro sin ejemplares
- **THEN** la edición se guarda con sus metadatos y su URL permanente
- **AND** su lista de bibliotecas tenedoras queda vacía sin error

### Requirement: Modo de descubrimiento y cobertura por fuente

Cada fuente SHALL declarar su modo de descubrimiento (`avanzada` o `novedades`) y si es de cobertura. El sistema SHALL usar la forma de búsqueda del modo declarado y SHALL NOT exigir ejemplares ni directorio a una fuente de cobertura.

#### Scenario: Descubrimiento avanzado

- **WHEN** una fuente declara `options.discovery="avanzada"`
- **THEN** la búsqueda usa el formulario avanzado con `xsqf01="*"`, `select03` y `subcat`
- **AND** el flujo es el mismo que el de Madrid y Andalucía

#### Scenario: Descubrimiento de Novedades

- **WHEN** una fuente declara `options.discovery="novedades"`
- **THEN** la búsqueda usa el formulario de Novedades con `FORM=5`, `select03=06`, el `select05` de la fuente y `subcat`, más los campos adicionales que declare la fuente
- **AND** no usa la consulta `*` del formulario avanzado

#### Scenario: Fuente de cobertura

- **WHEN** una fuente declara `options.coverage=true`
- **THEN** se guardan metadatos y URL permanente sin ejemplares
- **AND** no se le exige directorio ni lista de bibliotecas

### Requirement: Enlace permanente del registro

El sistema SHALL usar como URL permanente la declarada por la fuente (por ejemplo, el enlace canónico de la ficha) y, si no existe, SHALL construirla con el perfil y el `TITN`. SHALL NOT usar una URL de sesión.

#### Scenario: Enlace canónico

- **WHEN** la ficha declara un enlace canónico con el `TITN`
- **THEN** la edición y la API usan ese enlace
- **AND** el enlace no incluye el identificador de sesión

#### Scenario: Sin enlace canónico

- **WHEN** la ficha no declara un enlace canónico
- **THEN** se construye la URL con el perfil y el `TITN`
- **AND** no se usa la URL de la sesión de recolección

### Requirement: Calibración del perfil de fuente

El sistema SHALL ofrecer una operación idempotente que, para una fuente, compruebe el patrón de sesión y el código de formato de vídeo y actualice su perfil sin tocar otras fuentes. Si no encuentra un código de vídeo, SHALL informar y SHALL NOT inventarlo.

#### Scenario: Calibración correcta

- **WHEN** se calibra una fuente con un OPAC accesible
- **THEN** se actualizan su `session_pattern` y su `format_value` de vídeo
- **AND** las demás fuentes conservan su perfil

#### Scenario: Reejecución de la calibración

- **WHEN** se calibra dos veces la misma fuente
- **THEN** la segunda ejecución no cambia un perfil ya correcto
- **AND** informa del resultado

#### Scenario: Fuente sin código de vídeo

- **WHEN** la calibración no encuentra un código de formato de vídeo
- **THEN** informa del problema y deja el perfil sin cambios
- **AND** no inventa un código
