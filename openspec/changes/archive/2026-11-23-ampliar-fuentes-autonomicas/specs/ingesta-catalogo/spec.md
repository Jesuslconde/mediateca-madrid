# Spec Delta

## ADDED Requirements

### Requirement: Descubrimiento de fuentes de cobertura

El recolector SHALL descubrir los vídeos de una fuente de cobertura con el formulario de Novedades (`FORM=5`, `select03=06`, `select05=02`, `subcat`), y MUST guardar su cursor de paginación y el último identificador procesado en su propio trabajo. SHALL reanudar desde ese cursor sin compartirlo con otras fuentes.

#### Scenario: Descubrimiento de Novedades

- **WHEN** se ejecuta el descubrimiento de una fuente de cobertura
- **THEN** la petición usa el formulario de Novedades con el `subcat` y el filtro de videograbaciones de esa fuente
- **AND** no usa la consulta `*` del formulario avanzado

#### Scenario: Descubrimiento acotado

- **WHEN** se ejecuta el descubrimiento de una fuente de cobertura
- **THEN** los registros pertenecen al `subcat` de esa fuente y al formato de videograbaciones
- **AND** no se ingestan registros de otra comunidad en esa fuente

#### Scenario: Reanudar tras interrupción

- **WHEN** el descubrimiento de una fuente de cobertura se interrumpe
- **THEN** el siguiente trabajo de esa fuente reanuda desde su cursor guardado
- **AND** no reinicia desde el principio ni reutiliza el cursor de otra fuente

#### Scenario: Aislamiento de fallos

- **WHEN** una fuente de cobertura falla
- **THEN** su trabajo se detiene con el error de esa fuente
- **AND** las demás fuentes, incluidas las AbsysNet, siguen operando

### Requirement: Enriquecimiento de fuentes de cobertura

El recolector de cobertura MUST extraer de cada registro el identificador de la fuente, el título propio, la publicación, el año, el idioma, la descripción física, los géneros, las materias y, cuando existan, autores y notas. El título MUST ser el título propio sin la mención de responsabilidad.

#### Scenario: Registro con metadatos

- **WHEN** se enriquece un registro de una fuente de cobertura
- **THEN** la edición conserva sus metadatos normalizados y su URL permanente
- **AND** se registra la fecha de enriquecimiento

#### Scenario: Título con mención de responsabilidad

- **WHEN** el registro muestra `20.000 especies de abejas / dirección y guión de Estibaliz Urresola`
- **THEN** la edición guarda `20.000 especies de abejas`
- **AND** la mención de responsabilidad no forma parte del título

#### Scenario: Registro sin ejemplares

- **WHEN** el registro no declara ejemplares
- **THEN** la edición se guarda sin bibliotecas tenedoras
- **AND** el enriquecimiento termina sin error

## MODIFIED Requirements

### Requirement: Recolección sin estado de préstamo

El recolector MUST guardar la lista de bibliotecas y sucursales que la fuente declare para cada edición, y SHALL NOT consultar ni persistir el estado de préstamo. Una fuente de cobertura SHALL poder operar sin ejemplares: la edición se guarda sin bibliotecas tenedoras y sin error.

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

#### Scenario: Fuente de cobertura sin ejemplares

- **WHEN** una fuente de cobertura actualiza una ficha que no declara ejemplares
- **THEN** la edición se guarda sin bibliotecas tenedoras
- **AND** no se registra un fallo de recolección
