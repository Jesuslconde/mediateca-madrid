# Tasks

## 1. Configuración y migración

- [x] 1.1 Crear `services/enrich/scripts/migrate_andalucia_directory.sql` con un merge idempotente de `fuentes.options.directory` para `andalucia`; verificar ejecutándola dos veces sobre PostgreSQL sin duplicar la clave y sin modificar Madrid.
- [x] 1.2 Añadir un lector de configuración en `directory.py` que resuelva `options.directory` (`kind`, `url`, `mode`, `unit_types`) y mantenga `options.directory_path` como respaldo HTML; verificar con pruebas de fuente con y sin `directory`.
- [x] 1.3 Ampliar `services/enrich/tests/test_migrations.py` para comprobar la configuración del directorio de Andalucía y su idempotencia; verificar con `make test-migrations`.

## 2. Lector de datos abiertos y normalización

- [x] 2.1 Implementar `OpenDataDirectoryClient` y la factoría `build_directory_client(fuente)` con descarga JSON, timeout, reintentos con backoff y `User-Agent`; verificar con un fixture JSON y un servidor simulado.
- [x] 2.2 Implementar la normalización de `postcode` (entero, cadena y cero inicial), coordenadas con coma decimal, rangos geográficos y coordenadas vacías; verificar con pruebas unitarias de cada caso.
- [x] 2.3 Implementar la derivación de identidad desde `SUBC` de tres, dos y una parte y desde `icmsId` cuando no hay `SUBC`; verificar con pruebas que comprueben los códigos esperados y la reejecución idempotente.
- [x] 2.4 Implementar el filtro por `unit_types` con `Biblioteca` por defecto y la detección de bibliotecas móviles; verificar que los centros de documentación se cuentan como omitidos y que un bibliobús conserva municipio y código postal sin coordenadas.

## 3. Creación de bibliotecas y sucursales

- [x] 3.1 Ampliar `refresh_sucursales` con `create_missing` y las métricas `libraries_created` y `branches_created`; verificar con pruebas de creación, actualización y no duplicación.
- [x] 3.2 Ajustar el trabajo `branches` y `refresh-branches` para derivar `create_missing` de la política de la fuente (`match`/`create`) y conservar el comportamiento de Madrid; verificar con pruebas de ambos modos.
- [x] 3.3 Verificar que la creación desde el directorio no crea `ediciones` ni `ejemplares` y que no borra sucursales ausentes; añadir la prueba de integración correspondiente.

## 4. Integración y documentación

- [x] 4.1 Añadir una prueba de integración con el fixture andaluz que cree bibliotecas y sucursales, compruebe la cobertura y verifique que las filas de Madrid no cambian; ejecutarla con `make test-enrich`.
- [x] 4.2 Actualizar `README.md`, `docs/ARCHITECTURE.md` y `.env.example` con el directorio abierto de Andalucía, el comando `make branches fuente=andalucia` y la política `create`; verificar que los comandos documentados se ejecutan tal cual.
- [x] 4.3 Ejecutar `make test-enrich`, `make lint` y `make test-migrations`; verificar que no hay fallos ni avisos nuevos.

## Workflow follow-up

- Archivar el cambio después de que la revisión del proyecto esté satisfecha.
- Verificar que las specs principales reflejan el directorio abierto de Andalucía y que Madrid conserva su comportamiento.
