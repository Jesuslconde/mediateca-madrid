# Mediateca Madrid - API

API FastAPI de solo lectura para el portal. Consume los modelos y esquemas de `packages/shared` y lee PostgreSQL y Meilisearch; la ingesta se ejecuta en `services/enrich`.

## Comandos

Desde la raiz del monorepo:

```bash
make test-api
make lint
make openapi
```

La API comprueba `schema_meta.schema_version` al arrancar. Si el esquema no existe o no coincide con `SCHEMA_VERSION`, falla con un error legible.
