# modelo-catalogo Specification

## Purpose

Representar el catálogo en tres niveles (obra, edición y ejemplar) para agrupar las distintas versiones de una película y conservar la disponibilidad física por biblioteca.

## ADDED Requirements

### Requirement: Separación obra, edición y ejemplar

El modelo de datos MUST distinguir la obra (película), la edición (registro bibliográfico y soporte) y el ejemplar (copia física en una sucursal).

#### Scenario: Película con DVD y Blu-ray

- **WHEN** existen dos registros de la misma película, uno en DVD y otro en Blu-ray
- **THEN** ambos se agrupan bajo la misma obra
- **AND** cada uno conserva su propio `TITN`, soporte y ejemplares

### Requirement: Identificación estable

Cada edición MUST identificarse por su `TITN`; el EAN y la combinación de título, año y director SHALL usarse como señales secundarias de agrupación.

#### Scenario: Reproceso de un registro

- **WHEN** se vuelve a procesar un `TITN` ya existente
- **THEN** se actualiza el registro existente
- **AND** no se crea un duplicado

### Requirement: Normalización de metadatos

El parser MUST normalizar espacios, puntuación final, años, duración en minutos, idioma, país y roles de autoría antes de persistir.

#### Scenario: Duración extraída de la descripción física

- **WHEN** la descripción física contiene `1 DVD-Video (ca. 129 min)`
- **THEN** la edición guarda `duracion_min = 129`

### Requirement: Ejemplares y disponibilidad

Cada ejemplar MUST registrar biblioteca, sucursal, signatura, tipo de ejemplar, soporte y estado; los cambios de disponibilidad SHALL conservarse en un historial.

#### Scenario: Cambio de disponibilidad

- **WHEN** un ejemplar pasa de `Disponible` a `Prestado`
- **THEN** se actualiza su estado actual
- **AND** se añade una entrada al historial de disponibilidad

### Requirement: Personas y materias

Las personas MUST almacenarse una sola vez y relacionarse con la edición mediante un rol; las materias y géneros SHALL normalizarse para permitir facetas.

#### Scenario: Director y actor en la misma edición

- **WHEN** una edición tiene una persona como directora y otra como actor
- **THEN** ambas relaciones se guardan con roles distintos
- **AND** no se duplica la persona si ya existía
