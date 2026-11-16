# Spec Delta

## MODIFIED Requirements

### Requirement: Normalización de metadatos

El parser MUST normalizar espacios, puntuación final, años, duración en minutos, idioma, país y roles de autoría antes de persistir. El título MUST ser el título propio completo, sin mención de responsabilidad ni puntuación ISBD final.

#### Scenario: Duración extraída de la descripción física

- **WHEN** la descripción física contiene `1 DVD-Video (ca. 129 min)`
- **THEN** la edición guarda `duracion_min = 129`

#### Scenario: Título con subtítulo

- **WHEN** la ficha muestra `Historia cinematográfica de la Unión Europea : legislación cinematográfica europea /`
- **THEN** la edición guarda `Historia cinematográfica de la Unión Europea : legislación cinematográfica europea`
- **AND** no guarda la mención de responsabilidad

#### Scenario: Título con puntuación final

- **WHEN** el título termina en ` /`, ` :`, ` ;`, ` ,`, `.` o `=`
- **THEN** la puntuación final se elimina
- **AND** se conservan `?`, `!`, corchetes y paréntesis

#### Scenario: Título uniforme con puntuación final

- **WHEN** el título uniforme termina en puntuación ISBD
- **THEN** se elimina la puntuación final
- **AND** se conservan sus calificadores entre paréntesis
