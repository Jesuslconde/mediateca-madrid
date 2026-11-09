# Mediateca Madrid - backend

API, ingesta, normalizacion e indexacion del portal alternativo de videos y DVD/Blu-ray.

## Comandos

```bash
mediateca init-db
mediateca demo
mediateca index
mediateca harvest --query cine --max-pages 2
mediateca scheduler
mediateca refresh-availability
mediateca stats
```

La configuracion se lee de variables de entorno con prefijo `MEDIATECA_`.
