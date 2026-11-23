# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
