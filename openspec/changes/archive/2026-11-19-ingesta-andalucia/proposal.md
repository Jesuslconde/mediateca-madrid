# Proposal

## Why

La infraestructura multi-fuente ya existe, pero solo Madrid está registrada y operativa. Añadir la Red de Bibliotecas Públicas de Andalucía como segunda fuente real valida la identidad `record_id`, el aislamiento de sesiones, los trabajos por fuente y el reindexado antes de incorporar más redes.

## What Changes

- Registrar y sembrar la fuente `andalucia` con perfil AbsysNet: `base_url`, ruta, patrón de sesión, filtro de formato, retardo, política de captcha y estado habilitado.
- Usar `select03=05` (Videograbaciones) para recolectar vídeos del OPAC andaluz.
- Habilitar tareas de descubrimiento, enriquecimiento, TMDB e indexado para Andalucía desde la CLI, el scheduler y el dashboard.
- Mantener Madrid intacta: la migración no modifica sus datos, su perfil ni sus trabajos.
- Añadir fixtures y pruebas con la ruta `abnetcl.cgi`, incluyendo la misma `TITN` en Madrid y Andalucía.
- Documentar el alta, la configuración y la verificación de la segunda fuente.
- No se añade directorio de bibliotecas andaluz en esta fase; la tarea `branches` informará de que no hay directorio disponible sin fallar.

Fuera de alcance:

- Deduplicación o ficha única entre Madrid y Andalucía.
- Unificación de obras por TMDB/EAN entre fuentes.
- Directorio, direcciones y geocodificación de bibliotecas andaluzas.
- Cambios en la identidad `record_id`, el contrato OpenAPI o las listas.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `fuentes-opac`: añadir la fuente Andalucía como fuente registrada, habilitada y operativa.
- `operacion-despliegue`: añadir el alta idempotente de la fuente Andalucía sin alterar Madrid.

## Impact

- `services/enrich/scripts`: nueva migración idempotente de la fuente.
- `services/enrich`: configuración, CLI, scheduler, dashboard, fixtures y pruebas.
- `packages/shared`: sin cambios de modelo; se reutilizan `Fuente` y `record_id`.
- `services/api` y `apps/web`: sin cambios de contrato; la fuente aparece por los datos y la UI existente.
- Base de datos: nueva fila en `fuentes`; no se modifican identidades ni unicidades.
- Operación: aplicar la migración y lanzar la primera recolección de Andalucía; el reindexado de Madrid no es necesario.
