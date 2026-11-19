# Design

## Context

Ver `proposal.md` para la motivación. El cliente OPAC comparte `OpacClient._check_response` entre Madrid y Andalucía. La comprobación actual trata como captcha cualquier respuesta que contenga la subcadena `No soy un robot` o `chequeado 'No soy un robot'`.

La inspección del portal real de Andalucía el 2026-11-19 mostró:

- El catálogo completo (`select03=00`) declara 1.936.902 registros; las videograbaciones (`select03=05`) declaran 26.673.
- La paginación responde `200 OK` al menos hasta `DOC=26001`, sin página de desafío.
- Todas las páginas incluyen un nodo oculto de ayuda: `<span id="hmsgopa1075">Verifique que ha chequeado 'No soy un robot'.</span>`.
- No aparecen `grecaptcha`, `g-recaptcha` ni `g-recaptcha-response` en el listado.
- El parser actual extrae correctamente `TITN`, título y `DOC` del HTML real; el listado usa `js-TITN` y enlaces `ACC=165&DOC=`, no `TITN` en la URL.
- La paginación cambia el identificador de sesión de la ruta, pero las URLs de la página llevan el nuevo identificador y el cliente las sigue sin cambios. Las fichas de detalle responden tanto con la sesión inicial como con la rotada.

El cambio activo `ingesta-directorio-andalucia` partió de que el OPAC devolvía CAPTCHA y por eso se limitaba al directorio. Este diseño corrige esa premisa para el catálogo y no modifica el alcance del directorio.

## Goals / Non-Goals

**Goals:**

- Evitar que el texto de ayuda de AbsysNet detenga el descubrimiento de Andalucía.
- Conservar la detección de un desafío real y el flujo de FlareSolverr.
- Cubrir con fixtures la estructura real del listado y de la ficha andaluza.
- Verificar `discover --fuente andalucia` con una página y un lote pequeño.

**Non-Goals:**

- Determinar un umbral de captcha por volumen o hacer una prueba de carga.
- Cambiar el perfil OPAC, la migración de la fuente o la identidad `record_id`.
- Implementar el directorio abierto de bibliotecas, que pertenece al otro cambio activo.
- Tocar el esquema de PostgreSQL, la API, el portal o el contrato OpenAPI.

## Decisions

### D1. Detección en dos niveles

Se sustituye la búsqueda directa de la frase por una función dedicada:

```text
respuesta
   |
   +--> ¿contiene g-recaptcha / grecaptcha / recaptcha/api.js / g-recaptcha-response?
   |        |
   |        +-- sí --> captcha
   |
   +--> ¿contiene 'No soy un robot' fuera del nodo de ayuda?
            |
            +-- sí, y la pagina no tiene contenido de OPAC --> captcha
            +-- sí, pero la pagina tiene listado, ficha o formulario --> no captcha
```

Los marcadores de reCAPTCHA son la señal principal. La frase se conserva como respaldo para páginas de desafío antiguas o mínimas, pero solo después de descartar el nodo de ayuda conocido y de comprobar que la página no parece un listado (`c-docs_unit`), una ficha (`js-TITN`, `doc_title`) o el formulario de búsqueda (`abnformSearch`).

Alternativa descartada: borrar solo la frase `No soy un robot`. Si el portal cambia el identificador del nodo de ayuda, el falso positivo vuelve. La comprobación de contenido del OPAC evita depender de ese identificador.

### D2. Un único punto de detección

La detección vive en un helper de `harvester.py` usado por `_check_response`. `_solve_captcha` sigue llamando a `_check_response(..., count_captcha=False)` para validar la respuesta de FlareSolverr, de modo que una página resuelta con el texto de ayuda se considera correcta y no incrementa `captchas_failed`.

El flujo de FlareSolverr, las cookies, el `User-Agent` y los contadores por fuente no cambian.

### D3. Fixtures con la estructura real

Se actualiza `services/enrich/fixtures/andalucia/search_results.html` para reflejar el HTML real:

- `li.c-docs_unit` con `span.js-TITN`, `span.c-docs_title` y enlaces `ACC=165&DOC=`.
- Paginación con enlaces `ACC=161&DOC=11` y siguientes.
- Nodo oculto `hmsgopa1075` con el texto de ayuda.
- Ruta de sesión `/abnetcl.cgi/<sesion>/NT2`.

Se actualiza `detail_video.html` con `span.js-TITN`, `doc_title` y el mismo nodo de ayuda. Los fixtures se recortan a pocas fichas para no inflar el repositorio y no incluyen datos personales.

Alternativa descartada: mantener el fixture sintético actual, que no contiene el texto de ayuda y por eso no habría detectado el fallo.

### D4. Pruebas

- `test_harvester.py`: el listado andaluz con texto de ayuda no lanza `CaptchaRequired`; una respuesta con `g-recaptcha` sí lo lanza; una respuesta de FlareSolverr con texto de ayuda no cuenta como captcha fallido; Madrid conserva su comportamiento.
- `test_parser.py`: el fixture real produce `TITN`, título, `DOC` y descripción física; la ficha de detalle produce `TITN` y título.
- Prueba de regresión con un cliente simulado que recorre la primera página del fixture y crea los stubs esperados.

### D5. Verificación contra el portal real

Además de las pruebas con fixtures, se documenta y ejecuta una prueba de humo manual:

```bash
docker compose run --rm worker python -m mediateca discover --fuente andalucia --max-pages 1 --limit 5
```

La prueba no recorre el catálogo completo y sirve para confirmar que el portal real no introduce un desafío en la primera página. Si el entorno no tiene base de datos, se ejecuta el cliente con un transporte de prueba sobre el fixture; la prueba de humo real queda como verificación operativa.

## Risks / Trade-offs

- **Página de captcha sin marcadores conocidos** → se conserva la frase como respaldo y se añade una prueba con una página mínima que solo contiene `No soy un robot`.
- **Cambio del nodo de ayuda** → la detección no depende solo de `hmsgopa1075`; también exige ausencia de contenido de OPAC para tratar la frase como captcha.
- **Falso negativo en una página de desafío que incluya el listado** → los marcadores de reCAPTCHA son la señal principal; si el portal cambia a otro mecanismo, el fixture y la prueba de humo lo detectarán.
- **Coste de parsear HTML en cada respuesta** → la comprobación de marcadores es una búsqueda de cadenas; solo se parsea si la frase aparece y no hay marcadores, y el listado ya se parsea después para extraer resultados.
- **Datos del fixture** → se usan pocos registros públicos y se recortan; no se guarda el payload crudo ni datos personales.

## Migration Plan

1. Desplegar el cambio; no hay migración de base de datos ni reindexado.
2. Ejecutar `make test-enrich` y `make lint`.
3. Ejecutar la prueba de humo con `discover --fuente andalucia --max-pages 1 --limit 5` y comprobar que se crean stubs y que los contadores de captcha quedan a cero.
4. Lanzar un lote controlado de descubrimiento y, después, el enriquecimiento habitual.

Rollback: revertir el cambio de detección. Los stubs ya creados se conservan; no hay datos que migrar ni borrar.

## Open Questions

- Umbral real de captcha por volumen o por rate-limit: no se ha observado en la paginación probada y no bloquea este cambio. Si aparece en producción, la política de pausa por fuente ya lo cubre.
