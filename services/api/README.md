# Mediateca Madrid - API

API FastAPI de solo lectura para el portal. Consume los modelos y esquemas de `mediateca-shared` y lee PostgreSQL y Meilisearch; la ingesta se ejecuta en `mediateca-madrid-enrich`.

## Comandos

```bash
uvicorn mediateca.api.main:app --reload
pytest -q
ruff check src tests
```

La API comprueba `schema_meta.schema_version` al arrancar. Si el esquema no existe o no coincide con `SCHEMA_VERSION`, falla con un error legible.
