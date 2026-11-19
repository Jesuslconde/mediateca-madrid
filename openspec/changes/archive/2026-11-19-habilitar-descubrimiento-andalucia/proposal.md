# Proposal

## Why

La fuente `andalucia` está registrada, pero su descubrimiento se detiene en la primera búsqueda: el detector de captcha busca la cadena `No soy un robot` y el OPAC andaluz incluye esa frase como texto de ayuda oculto en todas sus páginas. La comprobación real del portal muestra que no hay una página de reCAPTCHA y que el catálogo de videograbaciones (26.673 registros) es paginable. El cambio activo de directorio partió de que el OPAC devolvía CAPTCHA; este cambio corrige esa premisa para el catálogo sin tocar el trabajo del directorio.

## What Changes

- Distinguir una página real de reCAPTCHA del texto de ayuda `hmsgopa1075` presente en el HTML de AbsysNet.
- Mantener intacto el flujo de FlareSolverr, los contadores de captcha y el aislamiento por fuente.
- Incorporar un fixture de listado y otro de ficha de Andalucía con la estructura real: `js-TITN`, enlaces `ACC=165&DOC=`, paginación `ACC=161&DOC=` y el texto de ayuda oculto.
- Añadir pruebas que demuestren que el listado andaluz no dispara un captcha y que una página de desafío real sí lo hace.
- Verificar `discover --fuente andalucia` con una página y un lote pequeño contra el portal real, sin recorrer el catálogo completo.

Fuera de alcance:

- Medir un supuesto límite de peticiones o captcha por volumen; no se ha observado un captcha real en la paginación probada.
- Cambiar el perfil OPAC de Andalucía, su migración o la identidad `record_id`.
- Implementar el directorio abierto de bibliotecas andaluzas, que pertenece al cambio `ingesta-directorio-andalucia`.
- Cambios en el esquema de PostgreSQL, la API, el portal o el contrato OpenAPI.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `ingesta-catalogo`: precisar la detección de reCAPTCHA para que el texto de ayuda de AbsysNet no se confunda con un desafío y para que el descubrimiento de una fuente use el listado real sin falsos positivos.

## Impact

- `services/enrich/src/mediateca/catalog/harvester.py`: detección de captcha y extracción de marcadores de desafío.
- `services/enrich/fixtures/andalucia`: listado y ficha con la estructura real del OPAC andaluz.
- `services/enrich/tests/test_harvester.py` y `test_parser.py`: cobertura del falso positivo, del captcha real y del parseo del listado.
- `docs/ARCHITECTURE_ENRICH.md`: aclaración de qué se considera una página de captcha.
- Sin cambios en `packages/shared`, `services/api`, `apps/web`, `contracts`, migraciones ni datos existentes.
