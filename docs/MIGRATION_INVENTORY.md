# Inventario de migracion

## Paquete compartido

Los modelos y esquemas que antes vivian en `mediateca-madrid-shared` se han integrado en:

```text
packages/shared/src/mediateca_shared/
```

- modelos SQLAlchemy
- esquemas Pydantic
- soportes y constantes de dominio
- `SCHEMA_VERSION` y comprobacion de esquema

## API y portal

- `backend/` -> `services/api/`
- `frontend/` -> `apps/web/`

## Ingesta

- repositorio independiente `mediateca-madrid-enrich` -> `services/enrich/`

## Artefactos eliminados

- `vendor/mediateca_shared-*.whl`
- dependencias `mediateca-shared==X.Y.Z`
- `docker-compose.yml` de api y enrich
- copia duplicada de `openapi.json` en el portal

El contrato unico vive en `contracts/openapi.json`.
