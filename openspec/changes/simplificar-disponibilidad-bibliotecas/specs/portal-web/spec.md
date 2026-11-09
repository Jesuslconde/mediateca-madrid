# portal-web Spec Delta

## REMOVED Requirements

### Requirement: Disponibilidad por biblioteca

**Reason**: El portal no puede garantizar el estado de préstamo en tiempo real; mantenerlo desactualizado induce a error.

**Migration**: La ficha muestra las bibliotecas que poseen el título con su signatura, tipo y soporte, y enlaza a la ficha del OPAC para consultar el préstamo actual.

## MODIFIED Requirements

### Requirement: Resultados y facetas

La página de resultados MUST mostrar título, año, soportes, géneros y bibliotecas tenedoras, y SHALL incluir filtros laterales combinables. SHALL NOT ofrecer un filtro por disponibilidad.

#### Scenario: Combinar filtros

- **WHEN** el usuario marca `DVD` y una biblioteca
- **THEN** la lista se actualiza con los registros que cumplen ambos filtros
- **AND** se conserva el término de búsqueda
- **AND** no aparece ninguna opción «Solo disponible»

### Requirement: Ficha de registro

La ficha MUST mostrar título, título uniforme, año, duración, idioma, país, sinopsis, géneros, materias, personas con rol, enlaces externos y acceso a la ficha del OPAC. SHALL NOT mostrar un estado de préstamo propio.

#### Scenario: Ficha de una película

- **WHEN** el usuario abre una película
- **THEN** ve su sinopsis, dirección, reparto y duración
- **AND** ve la lista de bibliotecas tenedoras con signatura y soporte
- **AND** dispone de un enlace a la ficha original del OPAC

## ADDED Requirements

### Requirement: Bibliotecas tenedoras y enlace al OPAC

La ficha SHALL agrupar los ejemplares por biblioteca y sucursal, indicar signatura, tipo y soporte, y enlazar cada biblioteca o la ficha del registro a la página del OPAC. SHALL NOT mostrar estado ni historial de préstamo.

#### Scenario: Biblioteca con Blu-ray

- **WHEN** una biblioteca posee un ejemplar Blu-ray del título
- **THEN** la ficha la muestra con la etiqueta `Blu-ray`
- **AND** indica la signatura y la sucursal
- **AND** no muestra si está prestado o disponible

#### Scenario: Enlace al OPAC

- **WHEN** el usuario pulsa el enlace de la ficha del OPAC
- **THEN** se abre en una pestaña nueva la ficha original del registro
- **AND** allí puede consultar el estado de préstamo actualizado
