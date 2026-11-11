# Design

## Context

Ver `proposal.md` para la motivación y las delta specs para el contrato de comportamiento. La API lee Meilisearch mediante `CatalogSearch` y PostgreSQL para las fichas; el portal consume la API. El índice lo escribe `mediateca-madrid-enrich`, que ya publicará `paises_origen` como atributo filtrable y faceta. La API comprueba `schema_meta.schema_version` contra `SCHEMA_VERSION` del wheel compartido al arrancar.

El campo `pais` del OPAC ya se muestra en la ficha. El nuevo filtro debe usar `paises_origen` de TMDB sin confundirlo con el `pais` del OPAC.

## Goals / Non-Goals

**Goals:**

- Permitir filtrar la búsqueda por uno o varios países de origen y devolver su faceta.
- Exponer `paises_origen` en los resultados y en la ficha de la API.
- Añadir el filtro y la visualización de países en el portal con etiquetas en español.
- Mantener la API de solo lectura y el contrato compartido como fuente de verdad.

**Non-Goals:**

- Obtener países de TMDB ni escribir el índice; eso corresponde a `pais-origen-tmdb`.
- Cambiar el `pais` del OPAC ni agrupar obras por país.
- Añadir filtros geográficos por región, continente o idioma.
- Introducir autenticación, escritura de datos ni un nuevo endpoint de metadatos.

## Decisions

### 1. Filtro y faceta en el adaptador de búsqueda

`FACET_FIELDS` incorpora `paises_origen`. `build_filters` acepta `paises_origen: list[str] | None` y genera una condición OR entre los códigos solicitados, combinada con el resto de filtros y con `detail_complete = true`. `CatalogSearch.search` y el router añaden el parámetro repetible `paises_origen`.

- **Por qué**: reutiliza el patrón existente de `soporte` y mantiene una sola consulta a Meilisearch.
- **Alternativa descartada**: filtrar en PostgreSQL; la app es de solo lectura y el resto de filtros viven en el índice.
- **Alternativa descartada**: aceptar nombres de país en español; los códigos ISO son estables y el índice ya los almacena así.

### 2. Contrato de API desde el wheel compartido

Se actualiza `mediateca-shared` a `0.2.0` en `backend/vendor/` y `backend/pyproject.toml`. `SearchHit` y `RecordDetail` ya incorporan `paises_origen`; `serialize_record` añade el campo de la edición. El router devuelve los hits de Meilisearch sin transformarlos, por lo que el campo llega directamente.

- **Por qué**: mantiene una única definición de los esquemas y evita duplicar tipos entre ingesta, API y portal.
- **Alternativa descartada**: declarar un esquema local en el backend; divergiría del contrato compartido y de los tipos generados.
- **Nota**: la API falla al arrancar si `schema_meta.schema_version` no es `2`; el despliegue debe respetar el orden shared → enrich → app.

### 3. Filtro multi-selección en el portal

`FacetFilters` añade un control `select` múltiple para `paises_origen`, con las opciones ordenadas por número de resultados y las etiquetas de `countryLabel`. El formulario envía valores repetidos; `buildSearchQuery` ya soporta arrays. La página de resultados incorpora los países a los filtros activos y `RecordCard`/la ficha muestran los países con sus etiquetas.

- **Por qué**: el control nativo funciona sin JavaScript adicional y es accesible por teclado.
- **Alternativa descartada**: una lista de checkboxes con todos los países; puede ser muy larga y desplazar el resto de filtros.
- **Alternativa descartada**: un `select` simple; impediría seleccionar varios países, que la API ya soporta.

### 4. Etiquetas ISO en el frontend

`lib/labels.ts` amplía el mapa `COUNTRIES` con los códigos ISO 3166-1 alfa-2 más habituales (`ES`, `US`, `GB`, `FR`, `DE`, `IT`, etc.) manteniendo los códigos MARC existentes. Si un código no está en el mapa, se muestra el propio código.

- **Por qué**: el índice guarda códigos y el portal debe mostrar nombres legibles sin duplicar la lógica en cada componente.
- **Alternativa descartada**: guardar nombres en español en el índice; ataría el dato al idioma y rompería la estabilidad del filtro.

### 5. Regeneración de contrato y tipos

Tras actualizar el wheel, se exporta `openapi.json` con `make openapi`, se sincroniza la copia de `frontend/contracts/openapi.json` y se ejecuta `npm run generate:api`. El build del portal verifica que los tipos generados cubren `paises_origen` y el nuevo parámetro.

- **Por qué**: el portal fija los tipos al contrato; una actualización manual se desincronizaría.
- **Alternativa descartada**: editar `api-types.ts` a mano; se perdería en la siguiente generación.

### 6. Atribución de TMDB en el layout

El pie de página global añade el texto de atribución de TMDB y un enlace a `https://www.themoviedb.org/`, visible en todas las páginas.

- **Por qué**: cumple las condiciones de uso de TMDB y no depende de que el usuario abra una ficha concreta.
- **Alternativa descartada**: mostrarlo solo en la ficha; incumpliría la visibilidad exigida en las páginas con datos derivados.

## Risks / Trade-offs

- [Faceta vacía antes del backfill] El índice no tendrá países hasta ejecutar el backfill y reindexar. → El filtro solo muestra los países presentes; el despliegue documenta el orden enrich → app.
- [Documentos antiguos sin el campo] Los documentos no reindexados no aparecerán al filtrar por país. → Se exige `mediateca index --reset` en el cambio de ingesta; el filtro no inventa resultados.
- [Códigos ISO sin etiqueta] Un país poco habitual puede mostrarse como código. → `countryLabel` devuelve el código como respaldo y se amplía el mapa con los códigos frecuentes.
- [Desajuste de esquema] La app falla al arrancar si el esquema no es `2`. → Despliegue coordinado shared → enrich → app y error legible ya existente.
- [Multi-selección nativa] Un `select` múltiple requiere mantener pulsada la tecla de selección. → Se añade una nota de ayuda y se conservan los filtros como chips; el resto de filtros no cambia.
- [Atribución incompleta] TMDB exige condiciones de uso y atribución. → Texto y enlace permanentes en el pie de página, revisados en el build del portal.
- [Rollback] Volver a la app anterior con la base en esquema `2` falla en `check_schema`. → El rollback debe coordinar shared y enrich; las columnas son aditivas, pero la versión de esquema debe alinearse en los tres repositorios.

## Migration Plan

1. Desplegar `pais-origen-tmdb` en `mediateca-madrid-enrich`: wheel `0.2.0`, migración, backfill y `mediateca index --reset`.
2. Sustituir el wheel en `backend/vendor/` y actualizar `backend/pyproject.toml` a `mediateca-shared==0.2.0`.
3. Implementar el filtro, la faceta y la serialización en el backend; ejecutar `pytest -q` y `ruff check src tests`.
4. Exportar el contrato con `make openapi`, sincronizar `frontend/contracts/openapi.json` y ejecutar `npm run generate:api`.
5. Añadir el filtro, la visualización y la atribución en el portal; ejecutar `npm run build`.
6. Desplegar la app y verificar `GET /api/search?paises_origen=ES`, la faceta, la ficha y el filtro del portal.

**Rollback**: si hay que volver a la versión anterior, desplegar de forma coordinada el wheel `0.1.0` y el esquema `1`; las columnas nuevas son aditivas y no destruyen datos. Mantener el índice reindexado no rompe la app anterior, que ignora `paises_origen`.
