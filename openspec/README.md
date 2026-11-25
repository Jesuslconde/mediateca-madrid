# OpenSpec

Esta carpeta contiene las especificaciones de comportamiento y el historial de cambios de Mediateca Madrid. No contiene código de runtime ni configuración de servicios.

La configuración está en [`config.yaml`](config.yaml):

- Esquema: `spec-driven`.
- Idioma de los artefactos: español.
- Encabezados estructurales y palabras clave `SHALL`/`MUST`: inglés.
- Contexto: monorepo con `services/api`, `services/enrich`, `apps/web` y `packages/shared`.

## Estructura

```text
openspec/
├── config.yaml
├── specs/
│   ├── api-portal/spec.md
│   ├── busqueda-facetas/spec.md
│   ├── cola-trabajos/spec.md
│   ├── contratos-compartidos/spec.md
│   ├── dashboard-ingesta/spec.md
│   ├── directorio-bibliotecas/spec.md
│   ├── enriquecimiento-tmdb/spec.md
│   ├── estado-ingesta/spec.md
│   ├── filtro-soporte/spec.md
│   ├── fuentes-opac/spec.md
│   ├── ingesta-catalogo/spec.md
│   ├── listas-compartidas/spec.md
│   ├── modelo-catalogo/spec.md
│   ├── observabilidad-ingesta/spec.md
│   ├── operacion-despliegue/spec.md
│   └── portal-web/spec.md
└── changes/
    └── archive/
```

### `specs`

Describe capacidades y requisitos del sistema consolidados. Cada subcarpeta corresponde a un área de comportamiento.

### `changes`

Contiene propuestas, diseños, deltas de especificaciones y tareas de un cambio. Los cambios completados se archivan en `changes/archive`.

Los artefactos archivados son históricos: pueden referirse a versiones de esquema, endpoints o decisiones que ya han evolucionado. No deben usarse como descripción del estado actual cuando contradigan el código o la documentación de módulos.

## Relación con la documentación

| Necesidad | Fuente recomendada |
|---|---|
| Arquitectura e implementación actual | [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) |
| API, ingesta, portal o modelos | `README.md` del módulo correspondiente |
| Comandos y despliegue | [`docs/OPERATIONS.md`](../docs/OPERATIONS.md) |
| Requisitos de producto | `openspec/specs` |
| Historia de una decisión | `openspec/changes/archive` |

Las especificaciones pueden expresar intención de producto; los `README` técnicos describen el comportamiento verificado en el código. Cuando exista una diferencia, debe revisarse el cambio que la originó antes de modificar cualquiera de los dos.

## Versionado del esquema

`SCHEMA_VERSION` está definido en [`packages/shared/src/mediateca_shared/version.py`](../packages/shared/src/mediateca_shared/version.py). Las referencias a versiones anteriores dentro de cambios archivados son históricas y no deben confundirse con el valor actual.

## Contribución

Al preparar un cambio:

1. Mantener los artefactos en español.
2. Conservar los encabezados estructurales y `SHALL`/`MUST` en inglés.
3. Vincular las specs afectadas.
4. Registrar tareas verificables.
5. Actualizar la documentación técnica del módulo cuando cambie la implementación.
6. Archivar el cambio solo después de completar y validar sus tareas.
