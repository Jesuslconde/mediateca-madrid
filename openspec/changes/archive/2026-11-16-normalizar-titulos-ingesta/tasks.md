# Tasks

## 1. Utilidad compartida de títulos

- [x] 1.1 Crear `packages/shared/src/mediateca_shared/titles.py` con `clean_title`, `strip_form_qualifier` y `split_responsibility`, aplicando NFC, limpieza de invisibles, colapso de espacios y puntuación final `[/ : ; , . =]`; verificar que el módulo se importa desde `services/enrich` y `services/api` sin errores.
- [x] 1.2 Añadir `packages/shared/tests/test_titles.py` con casos de puntuación final, `?`/`!`/corchetes/paréntesis, NBSP, caracteres invisibles, calificadores de forma y responsabilidad sin espacio; verificar con `make test-shared`.

## 2. Parser de fichas y listados

- [x] 2.1 Cambiar `parse_detail` para usar `.doc_title` como primera opción y `js-ntitl` solo como respaldo, limpiando el título y el título uniforme con la utilidad compartida; verificar con un test de `test_parser.py` basado en una ficha con subtítulo y barra final, y ejecutar `make test-enrich`.
- [x] 2.2 Cambiar `_parse_search_item` para usar `span.c-docs_title` como primera opción, seguido de `T245ab`, `T245` cortado por responsabilidad y `ntitl`; verificar con tests para título con mención de responsabilidad y con subtítulo, y ejecutar `make test-enrich`.
- [x] 2.3 Revisar los fixtures y tests existentes de `test_parser.py` para que el título esperado sea el título propio completo, sin `startswith` que oculte puntuación final; verificar con `make test-enrich`.

## 3. Candidatos de TMDB

- [x] 3.1 Actualizar `title_candidates` en `services/enrich/src/mediateca/catalog/tmdb.py` para limpiar títulos con la utilidad compartida, quitar calificadores de forma y separar responsabilidad con ` /` o ` / `; verificar con `make test-enrich`.
- [x] 3.2 Añadir a `services/enrich/tests/test_tmdb.py` casos para `Un amor (Película cinematográfica)`, `Ángel =`, `Alfredo el Grande ... /Marcos Ordóñez` y `The Prado Museum ... (Película cinematográfica)`; verificar con `make test-enrich`.
- [x] 3.3 Actualizar `docs/ARCHITECTURE_ENRICH.md` para describir que el emparejamiento elimina calificadores de forma y responsabilidad antes de consultar TMDB; verificar que el documento coincide con el comportamiento probado.

## 4. Backfill de títulos

- [x] 4.1 Implementar el comando `mediateca normalize-titles` en `services/enrich/src/mediateca/cli.py` con dry-run por defecto, `--apply`, `--limit` y `--reindex`; verificar que `docker compose run --rm worker python -m mediateca normalize-titles --limit 5` muestra el informe sin escribir.
- [x] 4.2 Implementar la extracción del título desde `marc["T245ab"]`, `marc["T245"]` cortado por responsabilidad, `marc["ntitl"]` y el título actual, actualizando solo las filas cuyo valor cambia y sin tocar `Obra`; verificar con tests de backfill sobre SQLite que las obras y los ejemplares no cambian.
- [x] 4.3 Añadir tests de idempotencia y de reindexado incremental de los TITN afectados; verificar que la segunda ejecución no cambia nada y que `index_titns` recibe solo los TITN modificados.
- [x] 4.4 Documentar el comando y su orden de operación (`dry-run`, copia de seguridad, `--apply --reindex`) en `services/enrich/README.md`; verificar que el comando documentado coincide con `python -m mediateca normalize-titles --help`.
- [x] 4.5 Ejecutar `make test-enrich` y `make lint` para validar los cambios de ingesta y del comando.

## 5. Integración y verificación

- [x] 5.1 Ejecutar `make test-shared test-enrich test-api` y verificar que pasan las pruebas de las tres capas.
- [x] 5.2 Ejecutar el dry-run completo sobre la base de datos de desarrollo y revisar el número de cambios y los ejemplos antes de aplicar.
- [x] 5.3 Con una copia de seguridad de PostgreSQL, ejecutar `normalize-titles --apply --reindex` y verificar que el índice responde y que la búsqueda de Blu-ray con país `ES` muestra títulos sin ` /`, ` :` ni ` =` finales.
- [x] 5.4 Comprobar una ficha concreta y su título uniforme, y verificar con una consulta SQL que el número de obras no ha cambiado tras el backfill.

## Workflow follow-up

- Ejecutar `/opsx-apply` cuando se apruebe el plan.
- Tras el backfill, valorar `mediateca tmdb-enrich --refresh --limit ...` por lotes para corregir países, portadas y enlaces TMDB de las ediciones afectadas.
- Archivar el cambio después de completar y revisar la implementación.
