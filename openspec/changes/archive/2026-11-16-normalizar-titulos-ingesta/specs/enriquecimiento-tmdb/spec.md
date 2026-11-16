# Spec Delta

## MODIFIED Requirements

### Requirement: Emparejamiento por título y año

El sistema MUST localizar la película en TMDB usando el título y el año de la edición y SHALL aceptar un resultado solo cuando el año coincida con una tolerancia máxima de un año. Antes de consultar SHALL eliminar la puntuación final, los calificadores de forma y la mención de responsabilidad. Si no hay un resultado suficientemente fiable, SHALL dejar la edición sin países y sin marcar como sincronizada.

#### Scenario: Coincidencia fiable

- **WHEN** el título normalizado y el año de la edición coinciden con un resultado de TMDB
- **THEN** el sistema selecciona ese resultado
- **AND** conserva el identificador de TMDB de la película

#### Scenario: Sin coincidencia fiable

- **WHEN** ningún resultado de TMDB coincide con el título y el año dentro de la tolerancia
- **THEN** la edición conserva su `pais` del OPAC y una lista `paises_origen` vacía
- **AND** no se marca como sincronizada con TMDB
- **AND** el fallo de emparejamiento queda registrado para revisión

#### Scenario: Título con puntuación del OPAC

- **WHEN** el título del OPAC termina en puntuación o separadores como ` / `
- **THEN** el sistema normaliza el título antes de consultar TMDB
- **AND** la puntuación final no impide la coincidencia

#### Scenario: Título uniforme con calificador de forma

- **WHEN** el título uniforme es `Un amor (Película cinematográfica)`
- **THEN** la consulta a TMDB usa `Un amor`
- **AND** el calificador no impide la coincidencia

#### Scenario: Título con signo igual final

- **WHEN** el título termina en `=`
- **THEN** la consulta a TMDB no incluye ese signo

#### Scenario: Mención de responsabilidad sin espacio

- **WHEN** el título contiene ` /Marcos Ordóñez` sin espacio después de la barra
- **THEN** la consulta a TMDB excluye la mención de responsabilidad
