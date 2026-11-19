# Spec Delta

## MODIFIED Requirements

### Requirement: Lista activa por navegador

El sistema SHALL conservar la lista en el servidor y SHALL recordar en una cookie persistente la lista activa del navegador. La cookie MUST compartirse entre todas las pestañas y SHALL restaurar la lista activa al reabrir el navegador. Al abrir una lista compartida, SHALL adoptarla como lista activa de todo el navegador. La cookie MUST NOT exigir una conexión segura cuando el portal se sirve por HTTP.

#### Scenario: Anadir sin lista previa

- **WHEN** el visitante pulsa el corazon y no existe cookie de lista
- **THEN** el sistema crea una lista y la marca como activa

#### Scenario: Abrir una lista en otro dispositivo

- **WHEN** el visitante abre el enlace de su lista en un navegador distinto
- **THEN** ve la lista completa
- **AND** la lista pasa a ser la activa de ese navegador

#### Scenario: Adoptar otra lista sin perder la anterior

- **WHEN** un navegador con una lista activa abre el enlace de otra lista
- **THEN** la lista abierta pasa a ser la activa
- **AND** la lista anterior no se elimina
- **AND** sigue accesible por su propio enlace

#### Scenario: Varias pestanas comparten la lista activa

- **WHEN** el visitante abre una segunda pestana del portal en el mismo navegador
- **THEN** ambas pestanas usan la misma lista activa
- **AND** el corazon de las ediciones refleja el mismo estado en ambas
- **AND** no se crea una lista distinta por pestana

#### Scenario: Cerrar y reabrir el navegador

- **WHEN** el visitante cierra el navegador y lo vuelve a abrir
- **THEN** el portal restaura la lista activa que tenia ese navegador
- **AND** `/mi-lista` muestra los titulos guardados
- **AND** el siguiente favorito se anade a esa misma lista

#### Scenario: Despliegue por HTTP

- **WHEN** el portal se sirve por HTTP sin TLS
- **THEN** el navegador acepta y conserva la cookie de lista activa
- **AND** la lista sigue disponible entre peticiones, pestanas y reinicios del navegador

#### Scenario: Despliegue por HTTPS

- **WHEN** el portal se sirve por HTTPS
- **THEN** la cookie de lista activa se emite como `Secure`
- **AND** no se envia por conexiones sin cifrar
