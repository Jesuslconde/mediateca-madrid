# Proposal

## Why

El parser guarda como título el campo corto `ntitl` de la ficha y el `T245` del listado, no el título propio visible. Por eso los títulos llegan a la base de datos, al índice y al portal con la puntuación ISBD final (` /`, ` :`, ` =`) y, en las fichas, sin el subtítulo. Ese mismo título truncado o con ruido se usa para emparejar con TMDB, así que el problema no es solo visual.

## What Changes

- Extraer el título propio completo desde `.doc_title` en las fichas y desde `span.c-docs_title` en los listados, usando `T245ab`, `T245` sin mención de responsabilidad y `ntitl` solo como respaldo.
- Normalizar los títulos antes de persistir: colapsar espacios, eliminar caracteres invisibles, normalizar a NFC y quitar la puntuación ISBD final (`/ : ; , . =`) sin tocar `?`, `!` ni corchetes.
- Aplicar la misma limpieza final al título uniforme, conservando sus calificadores entre paréntesis.
- Endurecer los candidatos de búsqueda de TMDB: quitar calificadores de forma, ignorar el `=` final y separar la mención de responsabilidad aunque no haya espacio después de `/`.
- Añadir un comando de backfill idempotente que recalcule los títulos existentes desde el MARC guardado, con modo seco y modo de aplicación, sin volver a recolectar del OPAC ni modificar las claves de agrupación de obras.
- Reindexar Meilisearch después del backfill y documentar el refresco opcional de TMDB con el comando existente.

No hay cambios incompatibles en la API ni en el esquema de datos: cambia el contenido normalizado de `titulo` y `titulo_uniforme`, no su forma.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `modelo-catalogo`: la normalización de metadatos exige título propio completo, sin mención de responsabilidad y sin puntuación ISBD final.
- `ingesta-catalogo`: el parser de fichas y de listados obtiene el título propio visible; nuevo backfill de títulos desde los metadatos guardados.
- `enriquecimiento-tmdb`: el emparejamiento normaliza calificadores de forma, `=` final y menciones de responsabilidad sin espacio antes de consultar TMDB.

## Impact

- `packages/shared`: nueva utilidad de limpieza de títulos y sus pruebas.
- `services/enrich`: parser de fichas y listados, candidatos de TMDB, comando de backfill, pruebas y documentación de operación.
- `services/api` y `apps/web`: sin cambios de código; muestran los títulos limpios tras el backfill y el reindexado.
- Datos: actualización de `titulo` y `titulo_uniforme` en ediciones existentes; no se tocan `Obra`, los ejemplares ni los campos TMDB.
- Operación: ejecutar el backfill en seco, aplicarlo, reindexar y, si se quiere corregir TMDB, lanzar `tmdb-enrich --refresh` sobre las ediciones afectadas.
- Fuera de alcance: quitar los calificadores entre paréntesis del título uniforme, el saneado solo visual en el frontend, `titulo_orden` y cualquier cambio de ordenación.
