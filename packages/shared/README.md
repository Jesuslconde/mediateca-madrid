# Mediateca Madrid - shared

Modelos SQLAlchemy, esquemas Pydantic y contratos compartidos entre la ingesta (`mediateca-madrid-enrich`) y la API/portal (`mediateca-madrid`).

## Uso

```bash
python -m build
pip install dist/mediateca_shared-0.3.0-py3-none-any.whl
```

La app y enrich fijan la misma version de `mediateca-shared`. `SCHEMA_VERSION` debe coincidir con la version registrada en la tabla `schema_meta` por la migracion de enrich.
