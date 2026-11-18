# Spec Delta

## MODIFIED Requirements

### Requirement: Lista sin cuenta

El sistema SHALL permitir crear una lista de favoritos sin registro, correo ni contrasena. Cada lista MUST quedar identificada por un token opaco e impredecible que actue como unica credencial de lectura y edicion. Cada elemento SHALL identificarse por `record_id` y no solo por `TITN`.

#### Scenario: Crear la lista con el primer favorito

- **WHEN** un visitante sin lista activa anade su primer favorito
- **THEN** el sistema crea una lista en el servidor
- **AND** devuelve un token y el enlace `/lista/{token}`
- **AND** no solicita ningun dato personal

#### Scenario: Sin datos personales almacenados

- **WHEN** se crea o edita una lista
- **THEN** el sistema no guarda correo, nombre, telefono ni direccion IP
- **AND** solo persiste `record_id`, un titulo opcional y marcas de tiempo

### Requirement: Anadir y quitar favoritos

El sistema SHALL permitir anadir una edicion a la lista y quitarla. Anadir una edicion ya presente MUST NOT duplicarla ni alterar su posicion. La identidad del elemento SHALL ser su `record_id`, de modo que dos ediciones con el mismo `TITN` en fuentes distintas SHALL ser elementos distintos.

#### Scenario: Anadir un favorito

- **WHEN** el visitante pulsa el corazon de una edicion que no esta en la lista
- **THEN** la edicion se incorpora a la lista con su `record_id`
- **AND** el corazon pasa a estado guardado

#### Scenario: Anadir dos veces la misma edicion

- **WHEN** se anade una edicion que ya estaba en la lista
- **THEN** la lista conserva una sola entrada para esa edicion
- **AND** no se reordena el resto

#### Scenario: Mismo TITN en dos fuentes

- **WHEN** el visitante guarda dos ediciones con el mismo `TITN` pero fuentes distintas
- **THEN** la lista conserva dos entradas distintas
- **AND** cada una muestra su fuente

#### Scenario: Quitar un favorito

- **WHEN** el visitante pulsa el corazon de una edicion guardada
- **THEN** la edicion desaparece de la lista
- **AND** el corazon vuelve a estado no guardado

## ADDED Requirements

### Requirement: Compatibilidad y migracion de listas

Las listas existentes SHALL migrarse sin perder elementos, asociando cada `TITN` guardado a `madrid:<titn>`. La API y el portal SHALL seguir aceptando un `TITN` sin fuente y SHALL resolverlo como Madrid.

#### Scenario: Lista historica

- **WHEN** se migra una lista con elementos guardados por `TITN`
- **THEN** cada elemento queda identificado por `madrid:<titn>`
- **AND** el numero de elementos no cambia
- **AND** los titulos guardados se conservan

#### Scenario: Enlace historico de favorito

- **WHEN** un cliente antiguo envia un `TITN` sin fuente
- **THEN** el sistema lo resuelve como `madrid:<titn>`
- **AND** no lo confunde con el mismo `TITN` de otra fuente
