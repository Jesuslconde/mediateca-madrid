# Design

## Context

Ver `proposal.md` para la motivación. El estado actual relevante:

- `Edicion.disponible`, `Ejemplar.disponible`, `Ejemplar.estado` e `HistorialDisponibilidad` se calculan al parsear cada ficha y se refrescan con `refresh-availability` y el job `availability` del scheduler.
- El índice de Meilisearch incluye `disponible` como campo filtrable y faceta; la API y el portal lo exponen como filtro «Solo disponible».
- El esquema se crea con `Base.metadata.create_all` y no hay herramienta de migraciones (Alembic u otra).
- Cada edición ya guarda `source_url` con la URL de su ficha original del OPAC.

## Goals / Non-Goals

**Goals:**

- Eliminar todo rastro de estado de préstamo del modelo, índice, API, portal y operación.
- Mantener los ejemplares como registro de tenencia (biblioteca, sucursal, signatura, tipo, soporte).
- Conservar la recolección periódica para metadatos y lista de bibliotecas.
- Ofrecer en la ficha un enlace a la ficha del OPAC para el estado de préstamo real.

**Non-Goals:**

- Añadir un campo `url` propio por biblioteca o geolocalización.
- Implementar comprobación de disponibilidad en vivo.
- Introducir Alembic u otro sistema de migraciones completo.

## Decisions

### 1. Eliminar columnas y tabla, no conservarlas como histórico

Se quitan `ediciones.disponible`, `ejemplares.disponible`, `ejemplares.estado` y la tabla `historial_disponibilidad`, y se eliminan sus relaciones del ORM.

- **Por qué**: el usuario descarta el dato de préstamo; conservarlo invita a mostrarlo desactualizado.
- **Alternativa descartada**: conservar el último estado como campo informativo. Se descarta para no mantener un dato engañoso ni su refresco.

### 2. El ejemplar sigue existiendo como unidad de tenencia

No se colapsan los ejemplares en una lista JSON dentro de la edición. Se mantiene `Ejemplar` con `biblioteca_id`, `sucursal_*`, `signatura`, `tipo_ejemplar`, `soporte` y `external_key`.

- **Por qué**: permite agrupar por biblioteca/sucursal, deduplicar y filtrar por biblioteca sin cambios estructurales.
- **Alternativa descartada**: guardar solo `bibliotecas: [nombre]` en la edición. Se descarta porque perdería signatura, sucursal y soporte por copia.

### 3. El parser deja de leer estado de préstamo

`ParsedEjemplar` pierde `estado` y `disponible`; `_parse_ejemplares` deja de interpretar `data-disp` y la columna de disponibilidad. `ParsedEdicion.disponible` se elimina.

- **Por qué**: evita acoplar el parseo a un estado volátil y simplifica los fixtures.
- **Alternativa descartada**: seguir parseando y descartar el dato. Se descarta por trabajo y ruido innecesarios.

### 4. Índice sin disponibilidad

Se retiran `disponible` de `FILTERABLE_ATTRIBUTES`, `FACET_FIELDS`, `build_document`, `build_filters` y la firma de `MeiliIndexer.search`. Se mantienen `bibliotecas` y `ejemplares` (conteo). El router de búsqueda devuelve `400` si el cliente envía `disponible`, en lugar de ignorarlo y devolver resultados sin filtrar.

- **Por qué**: el filtro por biblioteca sigue siendo útil; el de disponibilidad desaparece del contrato. Rechazar el parámetro evita que un cliente antiguo reciba resultados que cree filtrados.
- **Alternativa descartada**: dejar que FastAPI ignore el parámetro desconocido. Se descarta por silencioso y peligroso.
- **Migración del índice**: `ensure_index` reescribe settings y `index_editions(reset=True)` recarga documentos; los documentos antiguos con `disponible` se eliminan al reiniciar el índice.

### 5. Enlace al OPAC a nivel de edición

La ficha y la tabla de bibliotecas enlazan a `record.source_url`. No se añade URL por biblioteca.

- **Por qué**: el usuario eligió la ficha original del OPAC y ya disponemos de esa URL; añadir URLs por biblioteca requeriría una fuente de datos que hoy no existe.
- **Alternativa descartada**: campo `Biblioteca.url`. Se pospone hasta tener un origen fiable de URLs.

### 6. Migración de esquema sin Alembic

Se añade un script SQL idempotente (`scripts/migrate_disponibilidad.sql`) y un objetivo `make migrate-disponibilidad` que lo ejecuta sobre PostgreSQL. Para desarrollo, `make clean` sigue siendo válido.

- **Por qué**: `create_all` no elimina columnas ni tablas; el proyecto ya opera sin migraciones.
- **Alternativa descartada**: introducir Alembic. Se descarta por coste desproporcionado para un cambio de recorte.

### 7. Recolección periódica solo de metadatos

`_run_availability_job`, `refresh-availability`, su comando CLI y `MEDIATECA_SCHEDULER_AVAILABILITY_HOURS` se eliminan. El scheduler mantiene solo el job de recolección de fichas.

- **Por qué**: cumple la decisión de refrescar metadatos y lista de bibliotecas sin comprobar préstamos.
- **Alternativa descartada**: dejar el job desactivado por configuración. Se descarta para no mantener código muerto.

## Risks / Trade-offs

- **Clientes de la API rompen** (campos `disponible`, `estado`, `historial`, filtro `disponible`) → Es un cambio **BREAKING** declarado; se documenta en README y se actualiza el portal en el mismo cambio.
- **Bases de datos existentes conservan columnas/tabla** → Script SQL idempotente y objetivo de Makefile; se documenta en README.
- **Índice de Meilisearch con documentos antiguos** → Ejecutar `make index` con recarga completa tras el despliegue; `ensure_index` ya reescribe las settings.
- **Enlace único al OPAC para todas las bibliotecas** → Se etiqueta como «Ver ficha en el OPAC» para no prometer una página por sucursal.
- **Pérdida del filtro por disponibilidad** → Es intencionado; el usuario consulta el estado en el OPAC. No se ofrece sustituto en el portal.
- **Fixtures y tests acoplados a `data-disp`** → Se actualizan en el mismo cambio; el parseo ignora esa columna en lugar de fallar.

## Migration Plan

1. Desplegar el código con el modelo recortado.
2. Ejecutar el script de migración sobre PostgreSQL (`make migrate-disponibilidad`) para eliminar `historial_disponibilidad` y las columnas de disponibilidad.
3. Reindexar con recarga completa (`docker compose exec api mediateca index --reset`).
4. Verificar `/api/records/{titn}` sin campos de disponibilidad y con `source_url`, y `/api/search` sin faceta `disponible`.
5. Rollback: restaurar la versión anterior del código y reejecutar una recolección; las columnas eliminadas se recrean vacías con `init-db`, pero el historial previo no se recupera.
