# Design

## Context

Ver `proposal.md` para la motivación. El estado actual relevante:

- `Obra` es global y se crea en `get_or_create_obra()` con la clave `(titulo_uniforme, anio)`, con restricción única.
- `upsert_edicion()` asigna siempre `edicion.obra` a partir de la heurística, por lo que cualquier corrección manual se perdería en la siguiente reingesta.
- El índice de Meilisearch contiene un documento por edición y no incluye la obra. La API y el portal devuelven ediciones, no obras.
- El dashboard ya escribe catálogo de forma acotada: hoy solo la asignación manual de TMDB desde `/catalogo`, protegida por el token de administración.
- `SCHEMA_VERSION` vigente: `7`.

## Goals / Non-Goals

**Goals:**

- Permitir que el operador agrupe manualmente ediciones en una obra y que esa decisión prevalezca en el tiempo.
- Mostrar una sola tarjeta por obra en la búsqueda, con datos agregados de sus ediciones.
- Mantener el contrato actual de facetas y filtros sin introducir disponibilidad de préstamo.
- Entregar una migración idempotente y un procedimiento de despliegue verificable.

**Non-Goals:**

- Cambiar la heurística automática de agrupación.
- Permitir obras manuales duplicadas con el mismo título uniforme y año.
- Introducir facetas exactas por obra; esta iteración mantiene facetas por edición.
- Unificar ejemplares o disponibilidad entre ediciones.
- Reescribir la identidad global `record_id` ni las URLs del portal.

## Decisions

### D1. Marcas persistentes en edición y obra

Se añaden `ediciones.obra_manual`, `ediciones.obra_manual_at`, `obras.manual` y `obras.updated_at`.

`obra_manual` es la fuente de verdad de la decisión manual. `Obra.manual` permite distinguir una obra curada en el dashboard y saber si debe volver a automática cuando se queda sin ediciones manuales. Se mantiene la restricción única `(titulo_uniforme, anio)` para no admitir obras duplicadas.

Alternativa descartada: una tabla de agrupaciones separada. Duplicaría la relación obra-edición existente y complicaría la búsqueda y la ficha sin aportar nada en este alcance.

### D2. Precedencia manual en la ingesta

`upsert_edicion()` consulta primero si la edición ya existe y tiene `obra_manual = true`. En ese caso conserva `obra_id` y no ejecuta la heurística. Si la edición es nueva o automática, usa `get_or_create_obra()`. Cuando la obra resultante tiene `manual = true`, la edición queda también marcada como manual.

Así se evita que una reingesta rompa una agrupación curada, incluso si el título o el año cambian posteriormente.

### D3. Operaciones de agrupación

Nuevo módulo `services/enrich/src/mediateca/catalog/grouping.py`:

- `group_editions_into_obra()`: asigna las ediciones seleccionadas a una obra existente, marca como manuales todas las ediciones de esa obra y elimina las obras antiguas que quedan sin ediciones.
- `create_obra_and_group()`: reutiliza la obra con la misma clave `(titulo_uniforme, anio)` si existe; si no, la crea con `manual = true`; después agrupa.
- `ungroup_edition()`: limpia la marca manual, recalcula la obra automática y desmarca la obra anterior si ya no tiene ediciones manuales.

La eliminación de obras vacías se hace solo tras comprobar que no les queda ninguna edición. El FK `ediciones.obra_id` usa `ON DELETE CASCADE`, por lo que borrar una obra con ediciones eliminaría esas ediciones; la comprobación es obligatoria.

### D4. Página `/agrupacion`

Se añade una página HTML en `services/enrich/src/mediateca/dashboard/` con:

- filtros por texto (`q`), fuente, soporte y estado (`sin obra`, `manual`, `automática`);
- tabla paginada con checkboxes;
- un buscador de obra destino que reutiliza el mismo texto `q` de los filtros y muestra solo las obras coincidentes por título uniforme o año, con un máximo de 20, en lugar de un desplegable con todas las obras;
- campos de obra nueva y botones `Agrupar en obra existente`, `Agrupar en obra nueva` y `Volver a automático`;
- protección con `_has_write_access()` y redirección con mensaje, igual que las acciones actuales del dashboard.

La búsqueda de la obra destino y el filtro de ediciones comparten `q`: el texto se aplica a TITN/título en la tabla de ediciones y a título uniforme/año en las obras candidatas. Si `q` está vacío no se listan obras candidatas; el operador debe escribir texto para buscar el destino. Los demás filtros (fuente, soporte y estado) solo afectan a la tabla de ediciones.

La página es de lectura para quien no tiene token; solo las acciones POST escriben. Tras el commit se reindexan las ediciones afectadas. Si Meilisearch falla, la agrupación queda guardada y se avisa de que hay que ejecutar `make index`.

Alternativa descartada: un desplegable con todas las obras. No es usable con catálogos grandes y obliga a cargar la totalidad de las obras. Un campo independiente `obra_q` aislaría mejor ambos dominios, pero duplica el estado de búsqueda y obliga al operador a teclear dos veces; se prefiere reutilizar `q`.

Alternativa descartada: añadir la acción a la tabla de `/catalogo`. La agrupación necesita selección múltiple y elección de destino; una página propia mantiene el catálogo como vista de estado.

### D5. Índice de ediciones con referencia de obra

El documento de cada edición añade:

- `obra_id`;
- `obra_key`: `obra:<id>` si tiene obra, `edicion:<record_id>` si no;
- `obra_titulo`.

`obra_id` y `obra_key` se declaran filtrables. La búsqueda usa `distinct: "obra_key"` en la consulta de hits para devolver una edición representativa por obra. Las ediciones sin obra conservan su propio `obra_key`, por lo que no se colapsan entre sí.

Alternativa descartada: un índice separado de obras. Daría facetas exactas por obra, pero obliga a reconstruir la obra completa en cada enriquecimiento, a borrar documentos obsoletos cuando una edición cambia de obra y a duplicar la lógica de indexación. Para este alcance, el índice por edición con `distinct` es más simple y no deja documentos huérfanos.

### D6. Totales y facetas

La consulta de hits usa `distinct`; una segunda consulta, sin `distinct`, calcula las facetas y el total de ediciones. La respuesta devuelve:

- `total`: obras;
- `total_ediciones`: ediciones;
- `facets`: distribución por edición.

El portal muestra ambos totales para que los contadores de facetas sean interpretables. Las facetas siguen contando ediciones, no obras.

Alternativa descartada: usar `distinct` también en la consulta de facetas. Meilisearch aplica `distinct` antes de calcular facetas y los contadores quedarían reducidos a la edición representativa, lo que sería incorrecto.

### D7. Agregación en la API y ficha

Tras la búsqueda, la API recoge los `obra_id` de los hits y carga de PostgreSQL todas las ediciones de esas obras con sus ejemplares y bibliotecas. Cada hit se enriquece con:

- `ediciones_count`;
- unión de `soportes`;
- unión de `bibliotecas`;
- suma de `ejemplares`;
- `obra_titulo`;
- relleno de póster, año, duración o sinopsis cuando la edición representativa no los tenga.

La ficha de registro carga las ediciones hermanas de la obra y las expone en `ObraOut.ediciones` con los datos necesarios para enlazarlas. No se crea una ruta nueva de ficha.

### D8. Reindexado y versión de esquema

`SCHEMA_VERSION` pasa a `8`. La migración es idempotente. Al detectar el salto de versión, `init` reconstruye el índice con `--reset`, necesario para que todos los documentos tengan `obra_key`.

Al agrupar o desvincular se reindexan solo los `record_id` afectados mediante `index_titns()`. Las ediciones de la obra destino que no cambian de `obra_id` no necesitan reindexarse.

## Risks / Trade-offs

- **Las facetas cuentan ediciones, no obras** → el portal muestra `X obras · Y ediciones` y documenta la diferencia. Si más adelante se necesitan facetas exactas por obra, se añadirá un índice de obras sin cambiar el modelo.
- **`distinct` y paginación en Meilisearch** → verificar en la versión `v1.12` que `totalHits` y las páginas son correctos con `distinct`; si no lo fueran, usar `estimatedTotalHits` o calcular el total agrupado antes de paginar.
- **Reindexado síncrono en la petición** → son pocos documentos; si Meilisearch falla, la agrupación queda guardada y se avisa de que hay que reindexar. No se pierde la decisión manual.
- **Borrado accidental de una obra con ediciones** → la limpieza solo elimina obras cuyo recuento de ediciones es cero.
- **Obras manuales que reciben ediciones nuevas** → las ediciones que coinciden en clave se añaden y quedan marcadas como manuales; es el comportamiento deseado para una obra curada.
- **`q` compartido entre ediciones y obras** → un texto útil para filtrar ediciones puede no coincidir con el título uniforme de la obra destino, de modo que el operador tenga que ajustarlo para encontrar la obra. Si en uso real resulta confuso, se evaluará un campo `obra_q` independiente.
- **Ordenación por año o duración en obras con ediciones de años distintos** → se usa la edición representativa. La agrupación manual está pensada para la misma película, por lo que la diferencia es excepcional.
- **Consulta de agregación por página** → se cargan solo las ediciones de las obras devueltas y se usa `selectinload` para evitar N+1.
- **Rollback de código sin restaurar el esquema** → la migración añade columnas con valor por defecto y es compatible hacia atrás en lectura, pero el índice reconstruido y `SCHEMA_VERSION=8` requieren desplegar las dos imágenes coordinadas.

## Migration Plan

1. Copia de seguridad de PostgreSQL y del índice de Meilisearch; anotar `SCHEMA_VERSION=7`.
2. Desplegar `mediateca-batch` nueva.
3. Ejecutar `init`: aplica la migración, deja `SCHEMA_VERSION=8` y reconstruye el índice con las referencias de obra.
4. Desplegar `mediateca-web` nueva.
5. Verificar:
   - `/agrupacion` carga y permite agrupar;
   - las cuatro ediciones de *La vida padre* se agrupan y la búsqueda muestra una tarjeta;
   - una reingesta de una edición manual conserva la obra;
   - “Volver a automático” recalcula la obra;
   - la ficha lista las ediciones hermanas.
6. Si falla la verificación, restaurar la base y el índice desde la copia y volver a las imágenes anteriores.

## Open Questions

Ninguna que bloquee la implementación. La conveniencia de un índice de obras con facetas exactas se decidirá si el producto necesita contadores por obra en lugar de por edición.
