# operacion-despliegue Specification

## Purpose

Permitir que cualquier persona levante el portal completo en local o en un servidor desde un único repositorio, con dos imágenes, configuración por variables de entorno y verificaciones de salud.

## Requirements

### Requirement: Despliegue desde un monorepo

El repositorio MUST incluir un `docker-compose.yml` raíz con PostgreSQL, Meilisearch, inicialización, worker, dashboard, scheduler, API y portal. El despliegue SHALL construirse con dos imágenes: `mediateca-batch` para los procesos de ingesta y `mediateca-web` para la API y el portal.

#### Scenario: Arranque completo

- **WHEN** se ejecuta `docker compose up --build`
- **THEN** arrancan PostgreSQL, Meilisearch y el servicio de inicialización
- **AND** los servicios de ingesta y la API/portal usan sus respectivas imágenes
- **AND** la API y el portal quedan accesibles por sus puertos

#### Scenario: Construcción de imágenes

- **WHEN** se construye el stack
- **THEN** solo se generan las imágenes `mediateca-batch` y `mediateca-web`
- **AND** no se construyen imágenes separadas para API y para ingesta

### Requirement: Configuración por entorno

Todas las credenciales y URLs MUST configurarse mediante variables de entorno y SHALL existir un único `.env.example` documentado en la raíz.

#### Scenario: Cambio de clave de Meilisearch

- **WHEN** se cambia `MEILI_MASTER_KEY` en el entorno
- **THEN** la API, la ingesta y el indexador usan la nueva clave
- **AND** no se requiere modificar código

#### Scenario: Concurrencia del worker

- **WHEN** se configura `MEDIATECA_WORKER_CONCURRENCY` entre 1 y 5
- **THEN** el worker arranca ese número de hilos de reclamo
- **AND** el valor guardado desde el dashboard prevalece sobre el entorno
- **AND** el cambio se aplica al reiniciar el worker

### Requirement: Inicialización de base de datos

La imagen `mediateca-batch` MUST ofrecer comandos idempotentes para crear el esquema y el índice. La API SHALL NOT crear ni migrar el esquema y SHALL validar que la versión compartida es compatible al arrancar. El servicio `init` MUST ejecutarse antes que la API y el portal.

#### Scenario: Primer arranque

- **WHEN** se ejecuta el servicio `init`
- **THEN** se crean las tablas y el índice de Meilisearch si no existen
- **AND** se aplican las migraciones idempotentes
- **AND** puede ejecutarse de nuevo sin errores

#### Scenario: API sobre un esquema existente

- **WHEN** la API arranca contra una base ya inicializada
- **THEN** no ejecuta migraciones ni escrituras de esquema
- **AND** falla con un error legible si el esquema o la versión no son compatibles

### Requirement: Healthchecks

Los servicios críticos MUST declarar healthchecks y SHALL exponer un endpoint de salud agregado.

#### Scenario: Servicio caído

- **WHEN** PostgreSQL no responde
- **THEN** `/health` devuelve estado degradado
- **AND** Docker muestra el servicio como unhealthy

### Requirement: Verificación y documentación

El monorepo MUST incluir un README raíz con los comandos de arranque, operación, pruebas y publicación de imágenes, y SHALL incluir un Makefile con los atajos principales.

#### Scenario: Nuevo desarrollador

- **WHEN** una persona clona el repositorio y sigue el README
- **THEN** puede levantar el stack completo
- **AND** puede ejecutar las pruebas de shared, API e ingesta
- **AND** no necesita clonar repositorios adicionales

### Requirement: Almacenamiento compartido y orden de despliegue

PostgreSQL y Meilisearch SHALL ser compartidos por todos los servicios. La ingesta MUST ser el único dueño de las migraciones y de las escrituras del catálogo y del índice. La API SHALL leer el catálogo y el índice y SHALL escribir únicamente las tablas de listas; SHALL NOT modificar tablas del catálogo ni del índice. Los modelos MUST proceder de `packages/shared` y las dos imágenes SHALL construirse en el mismo commit.

#### Scenario: Migración antes de desplegar la API

- **WHEN** cambia el esquema o el contrato compartido
- **THEN** se actualizan los modelos y la migración en el mismo commit
- **AND** se reconstruyen `mediateca-batch` y `mediateca-web`
- **AND** el servicio `init` aplica las migraciones antes de arrancar la API

#### Scenario: Fallo de la API tras una migración

- **WHEN** la API no arranca con el esquema migrado
- **THEN** se puede revertir la API a la imagen anterior sin deshacer los datos
- **AND** la ingesta sigue siendo la única fuente de escritura del catálogo y del índice

### Requirement: Mantenimiento de listas en la inicialización

El servicio `init` SHALL eliminar las listas caducadas después de aplicar las migraciones y antes de arrancar la API. La limpieza MUST ser idempotente y SHALL NOT afectar a las listas vigentes.

#### Scenario: Limpieza en el arranque

- **WHEN** se ejecuta el servicio `init`
- **THEN** se eliminan las listas con `expires_at` vencido y sus elementos
- **AND** las listas vigentes permanecen intactas
- **AND** el servicio puede ejecutarse de nuevo sin errores

### Requirement: Publicación de imágenes

El repositorio MUST incluir un script de publicación que construya y suba las dos imágenes al registry configurado, etiquetadas con la versión unificada del repositorio.

#### Scenario: Publicar una versión

- **WHEN** se ejecuta el script de release con una versión
- **THEN** se publican `mediateca-batch` y `mediateca-web` con la etiqueta de versión y `latest`
- **AND** el stack de Portainer puede desplegar ambas imágenes sin cambios adicionales
