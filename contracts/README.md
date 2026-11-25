# Contrato OpenAPI

`contracts/openapi.json` es el contrato HTTP versionado de la API de Mediateca Madrid. Lo genera FastAPI a partir de las rutas y esquemas Pydantic de `services/api`.

El portal no interpreta este JSON en runtime. Lo usa en tiempo de desarrollo para generar tipos TypeScript en `apps/web/lib/api-types.ts`.

## Generación

Desde la raíz del monorepo:

```bash
make openapi       # API -> contracts/openapi.json
make web-types     # OpenAPI -> apps/web/lib/api-types.ts
make contracts     # ambos pasos
```

`make openapi` ejecuta `services/api/scripts/export_openapi.py` dentro del contenedor `api` y redirige stdout al archivo versionado. El exportador llama a `app.openapi()` y serializa con `ensure_ascii=False` e indentación 2.

No edites manualmente:

- `contracts/openapi.json`.
- `apps/web/lib/api-types.ts`.

Después de cambiar rutas, parámetros, esquemas o respuestas, ejecuta `make contracts` y revisa el diff.

## Contenido

El contrato describe:

- `/` y `/health`.
- `/api/search`.
- `/api/records/{record_id}`.
- `/api/libraries`.
- `/api/locations`.
- `/api/stats`.
- `/api/lists` y sus operaciones de lectura, alta, borrado y renombrado.
- Esquemas de búsqueda, fichas, obras, ejemplares, ubicaciones, bibliotecas, estadísticas y listas.

La documentación interactiva se sirve en `/docs`; `/redoc` también está disponible.

## Fuentes de verdad

| Artefacto | Autoridad |
|---|---|
| Rutas y handlers | `services/api/src/mediateca/api/routers` |
| Esquemas Pydantic | `packages/shared/src/mediateca_shared/schemas.py` |
| Contrato generado | `contracts/openapi.json` |
| Tipos del portal | `apps/web/lib/api-types.ts` |

Los modelos SQLAlchemy no generan directamente el contrato. Los serializadores de API transforman los modelos en los esquemas públicos.

## Compatibilidad

- Los campos nuevos deben ser opcionales o tener un default cuando sea posible.
- Eliminar o cambiar el tipo de un campo es un cambio incompatible.
- Un TITN suelto en `/api/records/{record_id}` se mantiene como compatibilidad y se resuelve a Madrid.
- Los identificadores nuevos usan `<fuente>:<titn>`.
- Los parámetros repetibles, como `soporte` y `paises_origen`, se serializan como query repetido.
- El portal usa `API_URL` en el servidor y no llama directamente a la API desde el navegador.

## Estado actual

El JSON versionado declara versión `0.7.11`, mientras el repositorio y la aplicación están en `0.8.2`. Debe regenerarse antes de publicar cambios de API.

El contrato contiene las rutas actuales, pero no refleja todos los comportamientos runtime:

- `POST /api/lists/{token}/items` devuelve 201 al crear y 200 si ya existe; OpenAPI solo declara 200.
- No documenta todos los errores 400/404/409/429/503.
- No declara `securitySchemes` porque las listas usan tokens portadores en la URL, no autenticación estándar.

Las pruebas de API comprueban algunos campos del contrato, pero no comparan el JSON versionado completo con `app.openapi()` en cada ejecución.

## Documentación relacionada

- [API](../services/api/README.md)
- [Portal](../apps/web/README.md)
- [Modelos compartidos](../packages/shared/README.md)
- [Operación](../docs/OPERATIONS.md)
