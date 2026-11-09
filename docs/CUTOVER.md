# Corte a la arquitectura de tres repositorios

## Orden

1. Publicar `mediateca-madrid-shared` `0.1.0` (wheel local o registro).
2. Arrancar `mediateca-madrid-enrich`:
   ```bash
   make up
   make migrate
   make init
   ```
3. Ejecutar una ingesta de prueba:
   ```bash
   make harvest q=cine pages=1 limit=2
   make index
   ```
4. Arrancar `mediateca-madrid`:
   ```bash
   docker compose up -d
   ```
5. Verificar:
   ```bash
   curl localhost:8000/health
   curl "localhost:8000/api/search?q=cine"
   docker compose -f ../mediateca-madrid-enrich/docker-compose.yml exec worker mediateca status
   ```

## Rollback

La etiqueta `pre-enrich-extraction` conserva el monorepo anterior con la ingesta integrada.

```bash
git checkout pre-enrich-extraction
docker compose up -d --build
```

La base de datos compartida mantiene el esquema compatible; no se ejecutan migraciones destructivas durante el corte. Si se necesita volver a enrich, repetir el orden shared → enrich → app.
