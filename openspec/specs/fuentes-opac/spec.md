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

Cada fuente MUST resolverse mediante un adaptador que abra sesión, ejecute la búsqueda, recupere fichas y construya la URL permanente de un registro. El adaptador SHALL recibir el perfil de la fuente y SHALL NOT compartir sesión, cookies ni contadores de captcha con otra fuente.

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
