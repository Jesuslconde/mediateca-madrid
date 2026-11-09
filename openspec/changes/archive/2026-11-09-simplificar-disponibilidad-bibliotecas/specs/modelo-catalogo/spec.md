# modelo-catalogo Spec Delta

## REMOVED Requirements

### Requirement: Ejemplares y disponibilidad

**Reason**: El estado de préstamo por ejemplar caduca y exige un refresco continuo que no garantiza exactitud; el portal solo necesita saber qué bibliotecas poseen el título.

**Migration**: Se conservan los ejemplares con biblioteca, sucursal, signatura, tipo y soporte. Se eliminan `ediciones.disponible`, `ejemplares.disponible`, `ejemplares.estado` y la tabla de historial de disponibilidad. El estado de préstamo se consulta en la ficha del OPAC mediante enlace.

## ADDED Requirements

### Requirement: Tenencia por biblioteca

Cada ejemplar MUST registrar biblioteca, sucursal, signatura, tipo de ejemplar y soporte. El sistema SHALL NOT almacenar estado de préstamo ni historial de disponibilidad, y SHALL deducir la lista de bibliotecas tenedoras a partir de los ejemplares.

#### Scenario: Ficha creada con ejemplares

- **WHEN** se crea la ficha de una edición con ejemplares en varias bibliotecas
- **THEN** cada ejemplar conserva su biblioteca, sucursal, signatura, tipo y soporte
- **AND** la edición expone la lista de bibliotecas que poseen el título

#### Scenario: Edición sin ejemplares

- **WHEN** una edición no tiene ejemplares registrados
- **THEN** su lista de bibliotecas tenedoras queda vacía
- **AND** no se inventa ninguna biblioteca

#### Scenario: Sin estado de préstamo

- **WHEN** se guarda o actualiza un ejemplar
- **THEN** no se persiste ningún campo de disponibilidad de préstamo
- **AND** no se añade ninguna entrada de historial de disponibilidad
