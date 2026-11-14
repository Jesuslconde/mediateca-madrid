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

## Rollback

Las bases de datos no cambian durante el corte. Para volver al despliegue anterior:

1. Restaurar el stack anterior de Portainer con las imagenes antiguas.
2. Mantener los repositorios `mediateca-madrid-enrich` y `mediateca-madrid-shared` archivados pero accesibles.

Las migraciones son idempotentes y no destructivas; no es necesario revertir datos para volver a la API anterior.
