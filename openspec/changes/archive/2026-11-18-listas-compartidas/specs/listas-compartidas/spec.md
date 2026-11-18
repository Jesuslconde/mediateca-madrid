# Spec Delta

## Purpose

Permitir que cualquier visitante guarde ediciones favoritas en una lista persistente y la comparta mediante un enlace editable, sin crear una cuenta ni aportar datos personales.

## ADDED Requirements

### Requirement: Lista sin cuenta

El sistema SHALL permitir crear una lista de favoritos sin registro, correo ni contrasena. Cada lista MUST quedar identificada por un token opaco e impredecible que actue como unica credencial de lectura y edicion.

#### Scenario: Crear la lista con el primer favorito

- **WHEN** un visitante sin lista activa anade su primer favorito
- **THEN** el sistema crea una lista en el servidor
- **AND** devuelve un token y el enlace `/lista/{token}`
- **AND** no solicita ningun dato personal

#### Scenario: Sin datos personales almacenados

- **WHEN** se crea o edita una lista
- **THEN** el sistema no guarda correo, nombre, telefono ni direccion IP
- **AND** solo persiste identificadores de ediciones, un titulo opcional y marcas de tiempo

### Requirement: Enlace como credencial de edicion

La URL `/lista/{token}` SHALL permitir leer y editar la lista a cualquier persona que la conozca. El sistema SHALL NOT distinguir propietario e invitado ni exigir otro permiso.

#### Scenario: Editar desde el enlace compartido

- **WHEN** una persona abre un enlace de lista valido
- **THEN** puede ver los titulos guardados
- **AND** puede anadir, quitar y renombrar sin iniciar sesion

#### Scenario: Token desconocido o caducado

- **WHEN** se solicita una lista con un token desconocido o caducado
- **THEN** el sistema responde con un error 404
- **AND** no revela si la lista existio

### Requirement: Lista activa por navegador

El sistema SHALL conservar la lista en el servidor y SHALL recordar en una cookie la lista activa del navegador. Al abrir una lista compartida, SHALL adoptarla como lista activa de ese navegador.

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

### Requirement: Anadir y quitar favoritos

El sistema SHALL permitir anadir una edicion a la lista y quitarla. Anadir una edicion ya presente MUST NOT duplicarla ni alterar su posicion.

#### Scenario: Anadir un favorito

- **WHEN** el visitante pulsa el corazon de una edicion que no esta en la lista
- **THEN** la edicion se incorpora a la lista
- **AND** el corazon pasa a estado guardado

#### Scenario: Anadir dos veces la misma edicion

- **WHEN** se anade una edicion que ya estaba en la lista
- **THEN** la lista conserva una sola entrada para esa edicion
- **AND** no se reordena el resto

#### Scenario: Quitar un favorito

- **WHEN** el visitante pulsa el corazon de una edicion guardada
- **THEN** la edicion desaparece de la lista
- **AND** el corazon vuelve a estado no guardado

### Requirement: Fichas desaparecidas

Cuando una edicion guardada ya no exista en el catalogo, la lista SHALL seguir mostrando el titulo guardado y SHALL indicar que la ficha ya no esta disponible, sin impedir el resto de la lista.

#### Scenario: Edicion retirada del catalogo

- **WHEN** una lista contiene una edicion que ya no existe
- **THEN** la lista muestra el titulo guardado con un aviso de ficha no disponible
- **AND** ofrece quitarla
- **AND** el resto de elementos se sigue mostrando

### Requirement: Titulo de la lista

La lista SHALL tener un titulo opcional editable de hasta 80 caracteres. El sistema SHALL recortar los espacios sobrantes y, si el titulo queda vacio, SHALL usar `Mi lista`.

#### Scenario: Renombrar la lista

- **WHEN** una persona edita el titulo y lo guarda
- **THEN** el nuevo titulo aparece en la lista y en el enlace compartido

#### Scenario: Titulo vacio o demasiado largo

- **WHEN** el titulo queda vacio o supera 80 caracteres
- **THEN** el sistema usa `Mi lista` si queda vacio
- **AND** recorta el texto a 80 caracteres si es mas largo

### Requirement: Limites y caducidad

Cada lista SHALL admitir como maximo 200 ediciones. El sistema SHALL limitar la creacion de listas por ventana de tiempo y SHALL eliminar las listas sin ediciones durante 180 dias.

#### Scenario: Lista llena

- **WHEN** se intenta anadir una edicion a una lista con 200 elementos
- **THEN** el sistema rechaza la operacion con un error legible
- **AND** la lista no cambia

#### Scenario: Lista caducada

- **WHEN** una lista lleva mas de 180 dias sin ediciones
- **THEN** el sistema la elimina
- **AND** su enlace responde con 404

#### Scenario: Exceso de creacion

- **WHEN** un mismo origen crea listas por encima del limite de la ventana
- **THEN** el sistema responde con 429
- **AND** no crea la lista

### Requirement: Enlace fuera de indices y de referencias

Las paginas de lista SHALL excluirse de la indexacion de buscadores y SHALL impedir que el token se propague en la cabecera `Referer` hacia sitios externos.

#### Scenario: Rastreador de buscador

- **WHEN** un buscador rastrea una pagina de lista
- **THEN** recibe una directiva de no indexacion

#### Scenario: Salida a un sitio externo

- **WHEN** el visitante pulsa un enlace al OPAC o a TMDB desde una lista
- **THEN** la peticion externa no incluye el token en `Referer`
