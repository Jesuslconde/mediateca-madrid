# Tasks

## 1. Spikes y calibración previa

- [x] 1.1 Calibrar las 10 redes AbsysNet: abrir el OPAC, extraer el patrón de sesión real y localizar el código de vídeo en `select03`; verificado con búsqueda real, todas devuelven 10 `li.c-docs_unit` y `select03=06`.
- [x] 1.2 Validar el parser actual contra un fixture real de Aragón, otro de Valencia y otro de País Vasco; verificado con fixtures reales y `parse_search_results`/`parse_detail`.
- [x] 1.3 Spike CCBIP: descartar Z39.50 y confirmar que el `OpacClient` y el parser actuales funcionan contra el OPAC del CCBIP; verificado con una búsqueda real y `parse_search_results`.
- [x] 1.4 Confirmar el formulario de Novedades (`FORM=5`, `xsqf99=1`, `select05=02`, `select03=06`, `subcat`) como descubrimiento; verificado con totales por comunidad (CLM 71.720, Galicia 56.545, Cataluña 48.401, Canarias 43.275, Baleares 11.565).
- [x] 1.5 Confirmar paginación (`ACC=161&DOC=N`), ficha (`ACC=165&DOC=N`) y enriquecimiento (`?TITN=<titn>&FORM=1`); verificado con una ficha real y `parse_detail`.
- [x] 1.6 Confirmar la URL permanente en `<link rel="canonical">` y que el `TITN` del CCBIP es numérico y válido (`18`, `5946466`); verificado en la ficha.
- [x] 1.7 Documentar la ruta viable en `design.md`; verificado que el diseño ya describe el modo de descubrimiento y el modo cobertura.

## 2. Extensión del perfil AbsysNet

- [x] 2.1 Añadir `options.discovery` a `OpacClient.search` con los modos `"avanzada"` y `"novedades"`; verificado con tests de la forma exacta de la petición de cada modo.
- [x] 2.2 Añadir `options.coverage` al flujo de descubrimiento y enriquecimiento; verificado con un test que una fuente de cobertura guarda la edición sin ejemplares y sin error.
- [x] 2.3 Leer `<link rel="canonical">` en `parse_detail` y usar `?TITN=<titn>` como respaldo; verificado con fixtures CCBIP y Madrid sin URL de sesión.
- [x] 2.4 Añadir tests de no regresión y aislamiento: Madrid y Andalucía siguen usando el modo `"avanzada"` y cada fuente mantiene su sesión y su cursor.
- [x] 2.5 Documentar `options.discovery`, `options.coverage`, `options.search_extra` y `options.detail_on_discovery` en `docs/ARCHITECTURE_ENRICH.md`; verificado que coincide con los tests.

## 3. Fuentes AbsysNet por red

- [x] 3.1 Crear `services/enrich/scripts/migrate_fuentes_autonomicas.sql` idempotente con las 10 fuentes deshabilitadas, su perfil y su modo de descubrimiento (`avanzada` o `novedades`); verificado con la migración ejecutada dos veces y sin cambios en Madrid ni Andalucía.
- [x] 3.2 Implementar `mediateca calibrate-source --fuente <codigo>` para actualizar `session_pattern` y `format_value` de una sola fuente; verificado con tests de calibración y del comando.
- [x] 3.3 Añadir pruebas de migración y de semilla de las 10 fuentes; verificado con `pytest tests/test_migrations.py` sobre PostgreSQL.
- [x] 3.4 Añadir fixtures y pruebas de parser por variante AbsysNet (Aragón, Valencia y País Vasco); verificado que cada fixture produce ediciones válidas.
- [x] 3.5 Documentar el alta, la calibración, la habilitación por oleadas y la reversión de una fuente AbsysNet; verificado en README y `docs/ARCHITECTURE_ENRICH.md`.
- [x] 3.6 Calibrar y habilitar las 10 fuentes una a una con un descubrimiento pequeño (`--max-pages 1 --limit`); verificado: las 10 devuelven 5 ediciones y el scheduler las cubre en sus tests.
- [x] 3.7 Indexar cada fuente habilitada; verificado que `/api/search?fuente=<codigo>` devuelve 5 resultados en las 10 y `source_url` usa el perfil de la fuente.
- [x] 3.8 Verificar que un fallo simulado en una red no detiene el descubrimiento ni el enriquecimiento de las demás; verificado con los tests de scheduler (deshabilitada/pausa) y los jobs y cursores por fuente.

## 4. Fuentes de cobertura CCBIP

- [x] 4.1 Crear `services/enrich/scripts/migrate_fuentes_cobertura.sql` idempotente con las 5 fuentes deshabilitadas, `adapter=absysnet`, `options.discovery="novedades"`, `options.coverage=true`, `subcat` y `select03=06`; verificado con la migración ejecutada dos veces.
- [x] 4.2 Añadir un fixture de la respuesta de Novedades del CCBIP y verificar que `parse_search_results` obtiene los registros y sus soportes.
- [x] 4.3 Añadir un fixture de la ficha del CCBIP y verificar que `parse_detail` obtiene `TITN`, título, año, idioma, país, soportes y la URL permanente.
- [x] 4.4 Añadir un test del descubrimiento de cobertura que compruebe el formulario de Novedades, el `subcat` y la paginación; verificado que no usa `xsqf01="*"`.
- [x] 4.5 Añadir un test de cobertura sin ejemplares; verificado que la edición se guarda, la lista de bibliotecas queda vacía y el job termina como completado.
- [x] 4.6 Adaptar el portal para mostrar ediciones de cobertura con título, soportes y enlace oficial, y estado vacío de bibliotecas; verificado con el test de API `test_record_de_cobertura_sin_ejemplares_expone_source_url` y el estado vacío de `LibrariesTable`.
- [x] 4.7 Documentar el modo cobertura, sus límites (sin ejemplares, desfase del CCBIP de junio de 2026) y el enlace oficial; verificado en README y `docs/ARCHITECTURE_ENRICH.md`.
- [x] 4.8 Habilitar y validar las 5 fuentes una a una; verificado: 5–7 ediciones por fuente, 0 ejemplares y URL canónica en la ficha.
- [x] 4.9 Indexar las 5 fuentes; verificado que aparecen en las facetas por fuente y que no introducen bibliotecas ni disponibilidad.

## 5. Verificación de integración

- [x] 5.1 Ejecutar `make test` y `make lint`; verificado: 394 pruebas de ingesta, 40 de API, 54 del paquete compartido, ruff y typecheck del portal.
- [x] 5.2 Ejecutar `make test-migrations` y `openspec validate ampliar-fuentes-autonomicas`; verificado: 5 pruebas de migración y change válido.
- [x] 5.3 Probar de extremo a extremo una búsqueda que mezcle Madrid, Andalucía, una fuente AbsysNet nueva y una de cobertura; verificado con Madrid, Andalucía, Aragón y Cataluña, facetas por fuente y `source_url`.
- [x] 5.4 Comprobar el dashboard: las 15 fuentes aparecen con su modo de descubrimiento, estado y último trabajo; verificado con la nueva tabla de fuentes y su test.
- [x] 5.5 Actualizar `README.md` y `docs/ARCHITECTURE_ENRICH.md` con la tabla de fuentes y el modo cobertura; verificado que coincide con las semillas.
- [x] 5.6 Simular la reversión: deshabilitar una fuente y comprobar que el scheduler deja de encolarla y que sus datos siguen consultables; verificado con `test_scheduler_ignora_fuentes_deshabilitadas`.

## Workflow follow-up

- Archivar el change cuando la revisión del proyecto esté satisfecha.
- Verificar el resultado archivado y que las specs principales recogen los deltas.
