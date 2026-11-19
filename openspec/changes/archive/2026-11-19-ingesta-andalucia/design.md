# Design

## Context

Ver `proposal.md` para la motivación. La infraestructura multi-fuente de `fuentes-opac` ya está desplegada: existe la tabla `fuentes`, la identidad `record_id`, el perfil OPAC por fuente, los trabajos y el scheduler por fuente, y el indexado por fuente.

El OPAC andaluz se ha inspeccionado en:

```text
https://www.juntadeandalucia.es/cultura/absys/abnopac/abnetcl.cgi/<sesion>?ACC=161
```

Es AbsysNet y comparte la estructura de formularios y resultados con Madrid. El formulario avanzado (`FORM=2`) expone `select03` como “Formato”, con el valor `05` para “Videograbaciones”. La sesión aparece en la ruta `/abnetcl.cgi/<sesion>`.

Prerrequisito ya aplicado: el indexado por fuente fallaba porque `index_editions(..., fuente_id=...)` llamaba a `build_document()` sobre el resultado de `iter_documents()`, que ya devuelve documentos. Se ha corregido con `iter_ediciones()` y una prueba de regresión.

## Goals / Non-Goals

**Goals:**

- Registrar Andalucía como fuente real y habilitada sin tocar Madrid.
- Reutilizar el adaptador AbsysNet y el parser existentes.
- Hacer que Andalucía aparezca en CLI, scheduler, dashboard y tareas por fuente.
- Dejar preparada la operación sin directorio de bibliotecas.

**Non-Goals:**

- Deduplicación o ficha única entre Madrid y Andalucía.
- Directorio, direcciones o geocodificación andaluza.
- Cambios en `record_id`, el contrato OpenAPI o el modelo de listas.
- Reindexado de Madrid o migración de datos históricos.

## Decisions

### D1. Perfil OPAC almacenado en `fuentes`

La fuente se siembra con este perfil:

| Campo | Valor |
|---|---|
| `codigo` | `andalucia` |
| `nombre` | `Red de Bibliotecas Públicas de Andalucía` |
| `adapter` | `absysnet` |
| `base_url` | `https://www.juntadeandalucia.es` |
| `opac_path` | `/cultura/absys/abnopac/abnetcl.cgi` |
| `session_pattern` | `/abnetcl.cgi/([A-Za-z0-9]+)` |
| `format_field` | `select03` |
| `format_value` | `05` |
| `enabled` | `true` |
| `delay` | `1.0` |
| `captcha_policy` | `pause` |
| `options` | `{}` (sin directorio) |

El perfil vive en la base y se puede ajustar sin reconstruir la imagen. `OpacClient.from_fuente` ya consume estos campos.

Alternativa descartada: otra variable global de entorno para la URL. Rompería el aislamiento y el dashboard no podría operar la fuente.

### D2. Migración idempotente

Se añade `migrate_andalucia.sql`, que inserta la fila con `ON CONFLICT (codigo) DO NOTHING`. No se reutiliza `migrate_fuentes.sql` para no alterar un cambio ya archivado. La migración no modifica `ediciones`, `bibliotecas`, `ejemplares`, `listas` ni `harvest_jobs`.

### D3. Reutilización del adaptador y del parser

No se crea un adaptador nuevo. `OpacClient` usa `FORM=2`, `select03=05`, `subcat=/`, `ACC=131` y las rutas `ACC=165`/`ACC=161`. Los fixtures `abnetcl.cgi` existentes se amplían con una ficha real o anonimizada de Andalucía para comprobar título, TITN, descripción física y ejemplares.

Alternativa descartada: un adaptador específico para Andalucía. Duplicaría sesión, captcha y paginación sin diferencias observadas.

### D4. Tareas y scheduler por fuente

No se cambia el scheduler: recorre `enabled_fuentes`. Al existir Andalucía habilitada, encola `discover`, `enrich` e `index` por fuente. El dashboard ya lista las fuentes habilitadas. `branches` para Andalucía devuelve “sin directorio disponible” sin escribir ni fallar.

### D5. Reindexado

El alta de Andalucía no cambia la identidad de Madrid ni el esquema. No se ejecuta `index --reset` por esta migración. El índice se llena con los trabajos de Andalucía cuando se ejecute su primera recolección. El arreglo del indexado por fuente es un prerrequisito para que el trabajo `index` de Andalucía funcione.

## Risks / Trade-offs

- **Captcha o bloqueo del OPAC andaluz** → la pausa es por fuente; Madrid sigue operando. Se registra en `paused_until` y en las métricas.
- **Cambios en el HTML de AbsysNet** → los fixtures y la prueba de humo detectan regresiones; el parser es compartido y ya está cubierto en Madrid.
- **Volumen inicial elevado** → empezar con `discover --fuente andalucia --max-pages` y `enrich --fuente andalucia --limit` controlados.
- **Sin directorio de bibliotecas** → no habrá cercanía ni direcciones andaluzas; la tarea `branches` lo informa sin fallar.
- **Duplicados entre fuentes** → aceptados en esta fase; la deduplicación es un cambio posterior.

## Migration Plan

1. Aplicar `migrate_andalucia.sql` con `make migrate` o el servicio `init`.
2. Verificar que `fuentes` contiene `andalucia` habilitada y que Madrid no cambió.
3. Ejecutar `discover --fuente andalucia --max-pages 1 --limit 20` y comprobar los stubs.
4. Ejecutar `enrich --fuente andalucia --limit 20` y `index --fuente andalucia`.
5. Verificar el dashboard, los trabajos y la búsqueda con `fuente=andalucia`.

Rollback: deshabilitar la fuente (`enabled=false`) o eliminar su fila solo si no se han ingestado datos; los datos de Madrid no se tocan. Si se han ingestado ediciones andaluzas, deshabilitar es el rollback seguro.

## Open Questions

- Ruta del directorio de bibliotecas andaluz, si se incorpora en un cambio posterior.
- Estrategia de deduplicación entre fuentes, fuera de este cambio.
