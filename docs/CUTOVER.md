# Corte al monorepo

## Orden

1. Publicar las imagenes con `make release`.
2. Actualizar el stack de Portainer con `deploy/portainer-stack.yml` y los valores de `MEDIATECA_REGISTRY` y `MEDIATECA_IMAGE_TAG`.
3. Desplegar el stack y esperar a que `init` termine.
4. Verificar:

```bash
curl localhost:8000/health
curl "localhost:8000/api/search?q=cine"
curl localhost:8080/health
```

## Migracion de fuentes

Este corte sube `SCHEMA_VERSION` a `7` y cambia la identidad de las ediciones a `record_id` (`<fuente>:<titn>`). Antes de desplegar:

1. Copia de seguridad de PostgreSQL y del indice de Meilisearch.
2. Desplegar la imagen nueva y ejecutar `init`; aplica la migracion y reconstruye el indice con `--reset` al detectar el salto de version.
3. Verificar busqueda, `/api/records/madrid:2101557`, `/api/records/2101557`, `/api/locations` y una lista historica.

## Rollback

La migracion de identidad no es compatible con la imagen anterior de la API. Para volver atras:

1. Restaurar la copia de seguridad de PostgreSQL y el indice anterior.
2. Restaurar el stack anterior de Portainer con las imagenes antiguas.

No intentes un rollback solo de la API sobre el esquema migrado.
