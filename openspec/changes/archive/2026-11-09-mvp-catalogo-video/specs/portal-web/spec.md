# portal-web Specification

## Purpose

Ofrecer un portal alternativo donde cualquier persona pueda buscar vídeos, distinguir DVD de Blu-ray y consultar en qué bibliotecas está disponible cada ejemplar.

## ADDED Requirements

### Requirement: Página de inicio con búsqueda

El portal MUST mostrar un buscador principal y accesos rápidos a los filtros `Solo DVD` y `Solo Blu-ray`.

#### Scenario: Acceso rápido a Blu-ray

- **WHEN** el usuario pulsa `Solo Blu-ray`
- **THEN** se abre la búsqueda con `soporte=Blu-ray`
- **AND** los resultados muestran la faceta de soporte activa

### Requirement: Resultados y facetas

La página de resultados MUST mostrar título, año, soportes, géneros y disponibilidad, y SHALL incluir filtros laterales combinables.

#### Scenario: Combinar filtros

- **WHEN** el usuario marca `DVD` y una biblioteca
- **THEN** la lista se actualiza con los registros que cumplen ambos filtros
- **AND** se conserva el término de búsqueda

### Requirement: Ficha de registro

La ficha MUST mostrar título, título uniforme, año, duración, idioma, país, sinopsis, géneros, materias, personas con rol y enlaces externos.

#### Scenario: Ficha de una película

- **WHEN** el usuario abre una película
- **THEN** ve su sinopsis, dirección, reparto y duración
- **AND** ve la lista de ejemplares por biblioteca y soporte

### Requirement: Disponibilidad por biblioteca

La ficha SHALL agrupar los ejemplares por biblioteca y sucursal e indicar signatura, tipo de ejemplar, soporte y estado.

#### Scenario: Ejemplar Blu-ray disponible

- **WHEN** una biblioteca tiene un Blu-ray disponible
- **THEN** la ficha lo muestra como `Blu-ray` y `Disponible`
- **AND** indica la signatura y la sucursal

### Requirement: Accesibilidad y estado vacío

El portal MUST ser navegable por teclado y SHALL mostrar un estado vacío claro cuando no haya resultados.

#### Scenario: Búsqueda sin resultados

- **WHEN** la búsqueda no devuelve registros
- **THEN** se muestra un mensaje con sugerencias
- **AND** se ofrece limpiar los filtros
