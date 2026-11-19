# Tasks

## 1. Detección de captcha

- [x] 1.1 Implementar en `harvester.py` un helper que distinga los marcadores reales de reCAPTCHA (`g-recaptcha`, `grecaptcha`, `recaptcha/api.js`, `g-recaptcha-response`) del texto de ayuda de AbsysNet, y usarlo en `_check_response`; verificar con las pruebas unitarias de detección.
- [x] 1.2 Mantener la comprobación de la respuesta de FlareSolverr y los contadores por fuente usando el mismo helper; verificar que una respuesta resuelta con texto de ayuda no incrementa `captchas_failed`.
- [x] 1.3 Añadir pruebas en `services/enrich/tests/test_harvester.py` para el listado andaluz con texto de ayuda, una página con marcador de reCAPTCHA, una página mínima solo con `No soy un robot` y una página de Madrid sin captcha; verificar con `pytest` sobre esas pruebas.
- [x] 1.4 Actualizar `docs/ARCHITECTURE_ENRICH.md` con la regla de detección y el caso del nodo de ayuda; verificar que la sección de captchas describe los marcadores y el respaldo de la frase.

## 2. Fixtures y parser

- [x] 2.1 Actualizar `services/enrich/fixtures/andalucia/search_results.html` con la estructura real: `li.c-docs_unit`, `span.js-TITN`, títulos visibles, enlaces `ACC=165&DOC=`, paginación `ACC=161&DOC=` y el nodo `hmsgopa1075`; verificar que `parse_search_results` extrae `TITN`, título y `DOC` de las fichas.
- [x] 2.2 Actualizar `services/enrich/fixtures/andalucia/detail_video.html` con `span.js-TITN`, `doc_title`, descripción física, ejemplares y el nodo de ayuda; verificar que `parse_detail` obtiene el `TITN` y el título esperados.
- [x] 2.3 Añadir una prueba de regresión en `services/enrich/tests/test_parser.py` y otra en `test_harvester.py` que recorran la primera página del fixture andaluz y creen los stubs esperados sin lanzar captcha; verificar con `make test-enrich`.

## 3. Verificación e integración

- [x] 3.1 Ejecutar `make test-enrich` y `make lint`; verificar que no hay fallos ni avisos nuevos.
- [x] 3.2 Ejecutar la prueba de humo `docker compose run --rm worker python -m mediateca discover --fuente andalucia --max-pages 1 --limit 5`; verificar que se crean stubs y que los contadores de captcha del trabajo quedan a cero.
- [x] 3.3 Verificar que un descubrimiento simulado de Madrid sigue funcionando y que su contador de captchas no cambia; ejecutar la prueba correspondiente de `test_harvester.py` o `test_jobs.py`.
- [x] 3.4 Añadir en `README.md` una nota breve sobre el estado operativo del descubrimiento de Andalucía y el comando de humo; verificar que el comando documentado se ejecuta tal cual.

## Workflow follow-up

- Archivar el cambio después de que la revisión del proyecto esté satisfecha.
- Verificar que la spec principal de `ingesta-catalogo` refleja la detección de captcha sin falsos positivos.
