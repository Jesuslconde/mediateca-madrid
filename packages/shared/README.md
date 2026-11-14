# Mediateca Madrid - shared

Modelos SQLAlchemy, esquemas Pydantic y `SCHEMA_VERSION` compartidos por la API (`services/api`) y la ingesta (`services/enrich`) dentro del monorepo.

## Uso

El paquete se instala desde la ruta local durante el build de las dos imagenes y en los entornos de desarrollo:

```bash
pip install ./packages/shared
```

No se publican wheels ni se fija una version entre repositorios. `SCHEMA_VERSION` debe coincidir con la version registrada en `schema_meta` por las migraciones de `services/enrich`.
