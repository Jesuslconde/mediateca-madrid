# Spec Delta

## ADDED Requirements

### Requirement: Directorio desde API de datos abiertos

El sistema SHALL admitir un directorio servido por una API de datos abiertos, además del directorio HTML. La lectura SHALL hacerse sobre la URL declarada por la fuente, SHALL aceptar JSON y SHALL NOT persistir el payload crudo. Cada fuente SHALL declarar el tipo y la URL de su directorio.

#### Scenario: Lectura del directorio abierto

- **WHEN** la fuente declara un directorio de tipo `opendata` con una URL JSON
- **THEN** la actualización lee todas las unidades publicadas en esa URL
- **AND** no guarda el JSON original en la base de datos

#### Scenario: Error temporal de la API

- **WHEN** la API responde con un error temporal o un timeout
- **THEN** la actualización se reintenta con backoff hasta el máximo configurado
- **AND** si persiste, la fuente queda sin actualizar sin afectar a las demás fuentes

#### Scenario: Fuente sin directorio

- **WHEN** una fuente no declara directorio
- **THEN** la actualización de esa fuente no se ejecuta
- **AND** el resto de fuentes sigue operando

### Requirement: Normalización de campos del directorio abierto

El sistema SHALL normalizar los campos antes de persistirlos: el código postal SHALL guardarse como cadena de cinco dígitos, las coordenadas con coma decimal SHALL convertirse a número y SHALL descartarse cualquier coordenada fuera de rango. Los campos de contacto y redes sociales SHALL leerse pero SHALL NOT persistirse en esta capacidad.

#### Scenario: Código postal entero

- **WHEN** la API devuelve `postcode` como entero `11402`
- **THEN** se guarda como cadena `11402`

#### Scenario: Código postal con cero inicial

- **WHEN** la API devuelve `postcode` como cadena `04001`
- **THEN** se guarda como cadena `04001` sin perder el cero inicial

#### Scenario: Coordenada con coma decimal

- **WHEN** la API devuelve `latitude` como `"36,6917266"` y `longitude` como `"-6,1334877"`
- **THEN** se guardan como números `36.6917266` y `-6.1334877`

#### Scenario: Coordenada ausente o inválida

- **WHEN** una unidad no trae coordenadas o trae valores fuera del rango geográfico
- **THEN** la latitud y la longitud quedan vacías
- **AND** se conservan el municipio y el código postal disponibles

### Requirement: Identidad estable de biblioteca y sucursal

El sistema SHALL derivar una identidad estable de cada unidad del directorio abierto. Para un `SUBC` de tres partes SHALL usar las dos primeras como código de biblioteca y el `SUBC` completo como código de sucursal. Para un `SUBC` de dos partes SHALL usar la primera como biblioteca y el `SUBC` completo como sucursal. Sin `SUBC` SHALL usar el identificador `icmsId` como código de biblioteca y SHALL NOT crear sucursal.

#### Scenario: SUBC de tres partes

- **WHEN** una unidad declara `SUBC=CA/CA08/218`
- **THEN** se crea o actualiza la biblioteca `CA/CA08`
- **AND** se crea o actualiza la sucursal `CA/CA08/218`

#### Scenario: SUBC de dos partes

- **WHEN** una unidad declara `SUBC=RBMALC/BMALC1`
- **THEN** se crea o actualiza la biblioteca `RBMALC`
- **AND** se crea o actualiza la sucursal `RBMALC/BMALC1`

#### Scenario: Unidad sin SUBC

- **WHEN** una unidad no declara `SUBC` y su `icmsId` es `orbe_bibliotecas/122`
- **THEN** se crea o actualiza la biblioteca `orbe_bibliotecas/122`
- **AND** no se crea ninguna sucursal

#### Scenario: Reejecución idempotente

- **WHEN** la actualización se ejecuta de nuevo sobre las mismas unidades
- **THEN** las bibliotecas y sucursales se actualizan en su sitio
- **AND** no se crean duplicados

### Requirement: Filtro de tipos y cobertura

El sistema SHALL permitir filtrar el directorio abierto por tipo de unidad. Por defecto SHALL ingerir solo las unidades cuyo tipo sea `Biblioteca`, y SHALL permitir incluir los centros de documentación mediante configuración. El resumen SHALL informar de unidades leídas, bibliotecas creadas, sucursales creadas, actualizadas y omitidas.

#### Scenario: Filtro por defecto

- **WHEN** la fuente no configura tipos de unidad
- **THEN** solo se procesan las unidades de tipo `Biblioteca`
- **AND** los centros de documentación se contabilizan como omitidos

#### Scenario: Inclusión de centros de documentación

- **WHEN** la fuente configura incluir los centros de documentación
- **THEN** se procesan también las unidades de tipo `Bib. Espec./Centro de Documentación`

#### Scenario: Resumen de cobertura

- **WHEN** termina una actualización del directorio abierto
- **THEN** el resumen muestra las unidades leídas, las bibliotecas creadas, las sucursales creadas, las actualizadas y las omitidas

### Requirement: Coordenadas de unidades móviles

El sistema SHALL NOT usar las coordenadas de bibliotecas móviles o bibliobuses como ubicación de una sucursal. SHALL conservar su municipio y su código postal cuando estén disponibles.

#### Scenario: Bibliobús con coordenadas

- **WHEN** una unidad móvil trae coordenadas
- **THEN** la latitud y la longitud quedan vacías
- **AND** se conservan el municipio y el código postal

## MODIFIED Requirements

### Requirement: Emparejamiento por código

El sistema SHALL emparejar el `SUBC` del directorio con los códigos de biblioteca y sucursal de la misma fuente y SHALL actualizar la entidad existente sin duplicarla. Cuando la política de la fuente sea `match`, SHALL omitir los códigos que no correspondan a una biblioteca conocida. Cuando la política sea `create`, SHALL crear la biblioteca o la sucursal que falten a partir de la ficha del directorio.

#### Scenario: Sucursal conocida

- **WHEN** una ficha del directorio de Madrid tiene `SUBC=RBMALC/BMALC1` y el catálogo ya tiene esa biblioteca y sucursal en Madrid
- **THEN** se actualizan el nombre, la dirección, el código postal y las coordenadas de la sucursal existente
- **AND** no se crea una sucursal duplicada

#### Scenario: Reproceso idempotente

- **WHEN** se vuelve a ejecutar la actualización sobre las mismas fichas
- **THEN** las sucursales se actualizan en su sitio
- **AND** el número de sucursales no aumenta

#### Scenario: Biblioteca desconocida

- **WHEN** una ficha del directorio de una fuente con política `match` declara una biblioteca que no existe en el catálogo de esa fuente
- **THEN** la ficha se omite
- **AND** la omisión se contabiliza en el resumen de la actualización

#### Scenario: Biblioteca desconocida en una fuente create

- **WHEN** una ficha del directorio de una fuente con política `create` declara una biblioteca que no existe en el catálogo de esa fuente
- **THEN** se crea la biblioteca con los datos de la ficha
- **AND** se crea o actualiza su sucursal cuando la ficha tenga código de sucursal

#### Scenario: Ficha de ámbito de biblioteca

- **WHEN** una ficha del directorio declara solo el código de biblioteca, sin código de sucursal
- **THEN** se actualizan los datos de ubicación de la biblioteca
- **AND** no se crea una sucursal adicional

#### Scenario: Código de otra fuente

- **WHEN** una ficha del directorio de Madrid declara un código que solo existe en otra fuente
- **THEN** la ficha se omite para Madrid
- **AND** no se actualiza ninguna biblioteca de la otra fuente

### Requirement: Actualización manual y cobertura

El sistema SHALL ofrecer un comando de actualización manual e idempotente del directorio y SHALL permitir encolar la misma actualización como trabajo `branches` desde el dashboard o la CLI. La actualización SHALL usar retardo configurable y límite opcional y SHALL informar de fichas leídas, con `SUBC`, con código postal, con coordenadas, emparejadas y omitidas. SHALL NOT borrar sucursales ausentes ni geocodificar direcciones en esta versión.

#### Scenario: Resumen de cobertura

- **WHEN** termina una actualización del directorio
- **THEN** el comando o el trabajo muestra el número de fichas leídas, con `SUBC`, con código postal, con coordenadas, emparejadas y omitidas

#### Scenario: Recarga de bibliotecas conocidas

- **WHEN** se ejecuta la tarea `branches` sobre una fuente con política `match`
- **THEN** solo se procesan las fichas de bibliotecas ya conocidas
- **AND** se crean o actualizan sus sucursales con la dirección y el código postal disponibles
- **AND** las fichas de bibliotecas desconocidas se contabilizan como omitidas
- **AND** no se crean bibliotecas nuevas

#### Scenario: Recarga con creación de bibliotecas

- **WHEN** se ejecuta la tarea `branches` sobre una fuente con política `create`
- **THEN** se crean las bibliotecas y sucursales que falten a partir del directorio
- **AND** se actualizan las que ya existan
- **AND** no se crean ediciones ni ejemplares

#### Scenario: Sucursal ausente

- **WHEN** una sucursal existente no aparece en una actualización posterior
- **THEN** la sucursal se conserva
- **AND** no se elimina automáticamente

#### Scenario: Coordenadas existentes

- **WHEN** una ficha actualizada no aporta coordenadas y la sucursal ya tenía coordenadas guardadas
- **THEN** se conservan las coordenadas existentes
- **AND** no se sobrescriben con valores vacíos

#### Scenario: Sin geocodificación

- **WHEN** una ficha no aporta coordenadas
- **THEN** el comando no invoca ningún servicio externo de geocodificación
- **AND** la resolución de la distancia queda en manos del portal mediante el código postal
