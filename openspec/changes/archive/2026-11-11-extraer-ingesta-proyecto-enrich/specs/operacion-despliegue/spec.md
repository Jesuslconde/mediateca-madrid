# Spec Delta

## MODIFIED Requirements

### Requirement: Despliegue con Docker Compose

Cada proyecto MUST incluir su propio `docker-compose.yml`. `mediateca-madrid-enrich` SHALL desplegar PostgreSQL, Meilisearch, worker y scheduler con volúmenes persistentes; `mediateca-madrid` SHALL desplegar API y portal conectados al almacenamiento compartido.

#### Scenario: Arranque completo

- **WHEN** se levantan los dos despliegues
- **THEN** enrich arranca PostgreSQL, Meilisearch, worker y scheduler
- **AND** la app arranca API y portal contra esos servicios
- **AND** la API y el portal quedan accesibles por sus puertos

### Requirement: Configuración por entorno

Todas las credenciales y URLs MUST configurarse mediante variables de entorno en cada repositorio y SHALL existir un `.env.example` documentado.

#### Scenario: Cambio de clave de Meilisearch

- **WHEN** se cambia `MEILI_MASTER_KEY` en el entorno compartido
- **THEN** la API, la ingesta y el indexador usan la nueva clave
- **AND** no se requiere modificar código

### Requirement: Inicialización de base de datos

Solo `mediateca-madrid-enrich` MUST ofrecer comandos idempotentes para crear el esquema y el índice. La app SHALL NOT crear ni migrar el esquema y SHALL validar que la versión compartida es compatible al arrancar.

#### Scenario: Primer arranque

- **WHEN** se ejecuta el comando de inicialización en enrich
- **THEN** se crean las tablas y el índice de Meilisearch si no existen
- **AND** puede ejecutarse de nuevo sin errores

#### Scenario: API sobre un esquema existente

- **WHEN** la API arranca contra una base ya inicializada
- **THEN** no ejecuta migraciones ni escrituras de esquema
- **AND** falla con un error legible si el esquema o la versión no son compatibles

### Requirement: Verificación y documentación

Cada repositorio MUST incluir un README con sus comandos de arranque, operación y pruebas, y SHALL incluir un Makefile con sus atajos principales.

#### Scenario: Nuevo desarrollador

- **WHEN** una persona clona la app o el proyecto de ingesta y sigue su README
- **THEN** puede levantar su parte contra el almacenamiento compartido
- **AND** la app no necesita ejecutar una ingesta para arrancar
- **AND** enrich puede ejecutar las pruebas del parser y del filtro de soporte

## ADDED Requirements

### Requirement: Almacenamiento compartido y orden de despliegue

PostgreSQL y Meilisearch SHALL ser compartidos entre ambos proyectos. Enrich MUST ser el único dueño de las migraciones y de las escrituras del catálogo y del índice; la app SHALL conectarse en modo lectura. El despliegue MUST seguir el orden shared, enrich y app.

#### Scenario: Migración antes de desplegar la app

- **WHEN** cambia el esquema o el contrato compartido
- **THEN** se publica primero el paquete compartido
- **AND** se aplican las migraciones en enrich
- **AND** después se despliega la app con la versión compatible

#### Scenario: Fallo de la app tras una migración

- **WHEN** la app no arranca con el esquema migrado
- **THEN** se puede revertir la app a la versión anterior sin deshacer los datos
- **AND** enrich sigue siendo la única fuente de escritura
