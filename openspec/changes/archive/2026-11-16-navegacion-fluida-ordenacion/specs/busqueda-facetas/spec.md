# Spec Delta

## MODIFIED Requirements

### Requirement: Ordenación

Los resultados SHALL poder ordenarse por relevancia, año de publicación, título o duración. Los órdenes por año y por duración SHALL desempatar por título ascendente.

#### Scenario: Orden por año descendente

- **WHEN** el usuario selecciona ordenar por año descendente
- **THEN** los resultados se muestran del más reciente al más antiguo

#### Scenario: Empate de año

- **WHEN** el usuario ordena por año y varias ediciones comparten el mismo año
- **THEN** las ediciones empatadas se muestran por título ascendente

#### Scenario: Empate de duración

- **WHEN** el usuario ordena por duración y varias ediciones comparten la misma duración
- **THEN** las ediciones empatadas se muestran por título ascendente
