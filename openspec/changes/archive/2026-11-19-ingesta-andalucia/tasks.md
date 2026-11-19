# Tasks

## 1. Prerrequisito de indexado

- [x] 1.1 Corregir `index_editions(..., fuente_id=...)` para construir cada documento una sola vez y añadir la prueba de regresión por fuente; verificado con `make test-enrich`.
- [x] 1.2 Verificar que el trabajo `index` por fuente del scheduler indexa solo la fuente del trabajo y no lanza el error de `personas`; ejecutar la prueba del handler en `tests/test_jobs.py`.

## 2. Fuente y migración

- [x] 2.1 Crear `services/enrich/scripts/migrate_andalucia.sql` idempotente con la fila `andalucia` y su perfil AbsysNet; verificar ejecutándola dos veces sobre PostgreSQL sin duplicados.
- [x] 2.2 Verificar que la migración deja `andalucia` habilitada y no modifica Madrid; comprobar con una consulta a `fuentes`, `ediciones` y `harvest_jobs`.
- [x] 2.3 Ampliar `services/enrich/tests/test_migrations.py` para cubrir el alta de Andalucía y su idempotencia; verificar con `make test-migrations`.

## 3. OPAC, fixtures y CLI

- [x] 3.1 Añadir un fixture de Andalucía con `abnetcl.cgi` y formato Videograbaciones; verificar que el parser obtiene TITN, título, descripción física y ejemplares.
- [x] 3.2 Añadir una prueba del perfil OPAC de Andalucía que compruebe `select03=05`, el patrón `/abnetcl.cgi/...` y el aislamiento de sesión frente a Madrid.
- [x] 3.3 Verificar `harvest`, `discover`, `enrich` e `index` con `--fuente andalucia` usando clientes simulados; comprobar que no reutilizan sesión, filtro ni contadores de Madrid.

## 4. Tareas, scheduler y dashboard

- [x] 4.1 Verificar que el scheduler encola trabajos para `andalucia` y Madrid por separado; comprobar que una fuente pausada no bloquea a la otra.
- [x] 4.2 Verificar que el dashboard muestra Andalucía en el selector y en las tareas, y que las acciones se crean con su `fuente_id`; añadir o ajustar las pruebas del dashboard.
- [x] 4.3 Añadir una prueba de aislamiento con la misma `TITN` en Madrid y Andalucía; verificar que existen dos ediciones y dos documentos de índice distintos.

## 5. Directorio de bibliotecas

- [x] 5.1 Verificar que `refresh-branches --fuente andalucia` y `enqueue-branches --fuente andalucia` informan de la ausencia de directorio sin fallar y sin modificar bibliotecas; añadir la prueba correspondiente.

## 6. Operación y verificación

- [x] 6.1 Actualizar `.env.example`, `README.md` y la documentación de despliegue con la fuente Andalucía, la migración y los comandos `--fuente`; verificar que los comandos documentados se ejecutan tal cual.
- [x] 6.2 Ejecutar la verificación integrada: `make test`, `make lint`, `make test-migrations` y `npm run build` en `apps/web`; verificar que no hay fallos.
- [ ] 6.3 Hacer una prueba de humo real con Andalucía: descubrir una página, enriquecer un lote, indexar la fuente y consultar `/api/search?fuente=andalucia`; verificar que Madrid sigue respondiendo igual.

## Workflow follow-up

- Archivar el cambio después de que la revisión del proyecto esté satisfecha.
- Verificar el resultado archivado y que las specs principales reflejan el alta de Andalucía.
