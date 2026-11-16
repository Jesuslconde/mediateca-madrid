# Design

## Context

Ver `proposal.md` para la motivación. El estado actual que condiciona el diseño:

- `parse_detail` prefiere `js-ntitl`, un título corto que puede terminar en ` :` o ` /` y perder el subtítulo (`services/enrich/src/mediateca/catalog/parser.py:468`).
- `_parse_search_item` prefiere `T245`, que incluye la mención de responsabilidad, y su fallback `a.c-docs_title` no coincide con el HTML real, que usa `span.c-docs_title` (`parser.py:374`).
- `clean(strip_trailing=True)` quita `/ : ; , .`, pero no `=` ni caracteres invisibles.
- TMDB ya usa `title_candidates`, pero no elimina calificadores de forma ni separa ` /Autor` sin espacio (`services/enrich/src/mediateca/catalog/tmdb.py:79`).
- `Edicion.marc` conserva el MARC normalizado, así que se pueden recalcular títulos sin volver a scrapear.
- `Obra` se agrupa por `titulo_uniforme`; no se debe reescribir esa clave en el backfill.
- Meilisearch se alimenta de `Edicion.titulo`, por lo que el índice se corrige al backfill y reindexar.

## Goals / Non-Goals

**Goals:**

- Guardar el título propio completo y limpio en las nuevas ingestas.
- Corregir las ediciones existentes desde el MARC guardado, sin recolectar de nuevo.
- Mejorar los candidatos que se envían a TMDB.
- Dejar el índice y la API con títulos limpios tras el backfill.

**Non-Goals:**

- Quitar los calificadores entre paréntesis del título uniforme para mostrarlo.
- Añadir `titulo_orden` o cambiar la ordenación.
- Introducir un saneado de títulos solo en el frontend.
- Reenriquecer automáticamente todos los matches de TMDB.
- Cambiar el esquema de la base de datos o el contrato OpenAPI.

## Decisions

### Utilidad compartida de limpieza de títulos

Se añade `packages/shared/src/mediateca_shared/titles.py` con funciones puras:

- `clean_title(value)`: normaliza a NFC, cambia NBSP por espacio, elimina caracteres de control y formato invisibles (`Cc`, `Cf`), colapsa espacios y quita la puntuación final `[/ : ; , . =]`. Conserva `?`, `!`, corchetes y paréntesis.
- `strip_form_qualifier(value)`: elimina uno o varios calificadores finales del tipo `(Película cinematográfica)`, `(Película cinematográfica : 2021)`, `(Videograbación)`, `(Documental)` o `(Serie)`. Se usa solo para candidatos de TMDB, no para lo que se guarda.
- `split_responsibility(value)`: corta por `\s+/\s*`, de modo que funciona con ` /Director` además de ` / Director`.

Se elige `packages/shared` porque lo usan ingesta y pruebas, y la API no necesita duplicar la lógica. Alternativa considerada: dejarlo en `services/enrich`; se descarta para que el backfill y los tests compartan exactamente las mismas reglas.

### Prioridad de extracción en el parser

En fichas:

```text
.doc_title (texto visible, título propio completo)
  -> js-ntitl (título corto, con limpieza final)
  -> error si no hay ninguno
```

En listados:

```text
span.c-docs_title (título propio visible)
  -> T245ab (título propio + subtítulo)
  -> T245 cortado por responsabilidad
  -> js-ntitl
  -> TITN como último recurso
```

`T245` se conserva en `marc` para trazabilidad. El `Título` del bloque `dl` no se usa porque incluye la mención de responsabilidad; `T245ab` ya aporta el título propio cuando existe.

`titulo_uniforme` se limpia con `clean_title`, pero se guarda con sus calificadores. Alternativa considerada: quitar el calificador al guardar; se descarta porque forma parte del título uniforme catalográfico y se perdería información.

### Candidatos de TMDB

`title_candidates` pasa a:

1. Limpiar cada título con `clean_title`.
2. Quitar el calificador de forma con `strip_form_qualifier`.
3. Separar la mención de responsabilidad con `split_responsibility`.
4. Añadir el título completo limpio y la cabeza sin responsabilidad, sin duplicados.

Así `Un amor (Película cinematográfica)` busca `Un amor`, `Ángel =` busca `Ángel` y `... /Marcos Ordóñez` busca `...`.

La comparación sigue usando `normalize_title`, que ya elimina acentos y puntuación.

### Backfill desde el MARC guardado

Nuevo comando `mediateca normalize-titles`:

- Por defecto hace un **dry-run**: recorre las ediciones, calcula el título nuevo y muestra cuántas cambiarían y ejemplos. No escribe nada.
- Con `--apply` actualiza `titulo` y `titulo_uniforme` solo cuando el valor calculado difiere.
- `--reindex` indexa los TITN afectados con `MeiliIndexer.index_titns`.
- `--limit` permite probar con un lote.
- No modifica `Obra`, `Ejemplar` ni campos TMDB.
- Es idempotente: una segunda ejecución no encuentra cambios.

Extracción para el backfill:

```text
marc["T245ab"]            (título propio completo)
  -> marc["T245"] cortado por responsabilidad
  -> marc["ntitl"]
  -> titulo actual
```

`titulo_uniforme` se recalcula con `clean_title` sobre el valor actual; no se intenta reconstruir desde cero porque el bloque `dl` no se guarda completo.

Alternativa considerada: migración SQL con `regexp_replace`; se descarta porque no puede elegir `T245ab`, ni separar responsabilidad, ni limpiar invisibles.

### Reindexado y TMDB

El backfill con `--reindex` reutiliza la indexación incremental por TITN, sin reconstruir todo el índice. Para TMDB no se resetean los matches automáticamente: el operador puede ejecutar el comando existente `tmdb-enrich --refresh` para reconsultar las ediciones afectadas. Esto evita una avalancha de peticiones y respeta los límites de TMDB.

## Risks / Trade-offs

- **Cambiar títulos puede alterar la agrupación de obras** → el backfill no toca `Obra`; las nuevas ingestas usarán el título limpio como clave de obra futura.
- **El backfill modifica datos existentes** → modo seco por defecto, `--limit`, informe de cambios y copia de seguridad de la base de datos antes de `--apply`.
- **Quitar calificadores de forma podría recortar un paréntesis legítimo** → lista cerrada de términos de calificador; si no coincide, el título se deja intacto.
- **`doc_title` puede faltar en alguna ficha** → se mantiene `ntitl` como respaldo y se limpia la puntuación final.
- **El título uniforme sigue mostrando el calificador entre paréntesis** → queda fuera de alcance; se puede abordar en un cambio de presentación.
- **Los matches TMDB existentes pueden seguir siendo incorrectos** → se documenta `tmdb-enrich --refresh`; no se ejecuta automáticamente.
- **Coste del backfill sobre todo el catálogo** → ejecución por lotes y reindexado incremental de los TITN afectados.

## Migration Plan

1. Desplegar la utilidad compartida, el parser, los candidatos de TMDB y el comando de backfill.
2. Ejecutar `normalize-titles --limit 100` y revisar los ejemplos.
3. Ejecutar el dry-run completo y comprobar el número de cambios.
4. Hacer copia de seguridad de PostgreSQL.
5. Ejecutar `normalize-titles --apply --reindex`.
6. Verificar el portal con una búsqueda real, por ejemplo la de Blu-ray con país `ES`.
7. Opcionalmente, ejecutar `tmdb-enrich --refresh` por lotes y revisar países y portadas.

Rollback: restaurar la copia de seguridad de PostgreSQL y desplegar las imágenes anteriores. No hay migraciones de esquema ni cambios destructivos.

## Open Questions

Ninguna que bloquee el diseño. La presentación del título uniforme sin calificadores y la ordenación natural de títulos quedan como cambios futuros independientes.
