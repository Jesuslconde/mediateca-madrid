# Documentación técnica

## Módulos

| Módulo | Documentación | Responsabilidad |
|---|---|---|
| API | [`services/api/README.md`](../services/api/README.md) | Consulta del catálogo, búsqueda y listas de favoritos |
| Ingesta | [`services/enrich/README.md`](../services/enrich/README.md) | Descubrimiento, enriquecimiento, cola, indexación y administración |
| Portal | [`apps/web/README.md`](../apps/web/README.md) | Interfaz Next.js y consumo de la API |
| Compartido | [`packages/shared/README.md`](../packages/shared/README.md) | Modelos SQLAlchemy, esquemas Pydantic y versión del esquema |

## Infraestructura y herramientas

| Carpeta | Documentación |
|---|---|
| Imágenes Docker | [`docker/README.md`](../docker/README.md) |
| Portainer | [`deploy/README.md`](../deploy/README.md) |
| Contrato HTTP | [`contracts/README.md`](../contracts/README.md) |
| Scripts de mantenimiento | [`scripts/README.md`](../scripts/README.md) |
| Especificaciones | [`openspec/README.md`](../openspec/README.md) |

## Arquitectura y operación

- [`ARCHITECTURE.md`](ARCHITECTURE.md): límites entre componentes y flujo general de datos.
- [`ARCHITECTURE_ENRICH.md`](ARCHITECTURE_ENRICH.md): detalle de descubrimiento, persistencia, cola e indexación.
- [`OPERATIONS.md`](OPERATIONS.md): arranque, comandos, migraciones, releases, despliegue y atribución.
- [`CUTOVER.md`](CUTOVER.md): procedimiento de transición.
- [`MIGRATION_INVENTORY.md`](MIGRATION_INVENTORY.md): inventario de migraciones.

## Contratos

El contrato HTTP versionado es [`contracts/openapi.json`](../contracts/openapi.json). El portal genera `apps/web/lib/api-types.ts` a partir de él; no edita ese archivo manualmente.

## Especificaciones

Los cambios de diseño y sus artefactos se mantienen en [`openspec`](../openspec). La documentación de esta carpeta describe la implementación y operación actual.
