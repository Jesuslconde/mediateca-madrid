# Mediateca Madrid

Portal alternativo de busqueda de videos, DVD y Blu-ray de las bibliotecas publicas de la Comunidad de Madrid.

El repositorio es un monorepo con la API, el portal, la ingesta y los modelos compartidos. Se construyen dos imagenes: `mediateca-batch` para los procesos de ingesta y `mediateca-web` para la API y el portal.

## Estructura

```text
services/api/       API FastAPI de solo lectura
services/enrich/    ingesta, worker, scheduler, dashboard y migraciones
apps/web/           portal Next.js
packages/shared/    modelos SQLAlchemy, esquemas Pydantic y SCHEMA_VERSION
contracts/          contrato OpenAPI unico
deploy/             stack de Portainer
docs/               arquitectura y operacion
openspec/           especificaciones y cambios
```

## Inicio rapido

```bash
cp .env.example .env
make up
```

Abre:

- Portal: <http://localhost:3000>
- API: <http://localhost:8000/docs>
- Dashboard: <http://localhost:8080>
- Meilisearch: <http://localhost:7700>

El servicio `init` crea las tablas, aplica las migraciones idempotentes y prepara el indice antes de arrancar el worker y la API.

## Comandos

```bash
make help
make up
make down
make logs
make ps
make init
make migrate
make harvest q=cine pages=2 limit=20
make harvest q=cine pages=2 limit=20 fuente=madrid
make branches
make branches-enqueue
make index
make dashboard
make psql
make test
make lint
make fmt
make openapi
make web-types
make check-schema
```

Las pruebas se ejecutan en las imagenes correspondientes, de modo que API e ingesta no comparten un unico entorno virtual.

## Sucursales y orden por cercania

`make branches` actualiza direcciones, codigos postales y coordenadas de las sucursales desde el Directorio de Bibliotecas de la Comunidad de Madrid. El comando es idempotente, no borra sucursales ausentes y no geocodifica direcciones: si una ficha no trae coordenadas, el portal usa el centroide de su codigo postal. Para una prueba limitada: `make branches branches_limit=20`.

La misma actualizacion puede encolarse como tarea manual con `make branches-enqueue` (o `python -m mediateca enqueue-branches`) y desde el boton "Recargar direcciones de bibliotecas" del dashboard. Esa tarea solo procesa bibliotecas que ya existen en el catalogo: actualiza sus direcciones y crea o actualiza sus sucursales. Las fichas de bibliotecas desconocidas se omiten y no se crean bibliotecas nuevas. El scheduler no la ejecuta automaticamente.

En la ficha de un registro se puede elegir un codigo postal para ordenar las bibliotecas por cercania. Sin seleccion, el orden es alfabetico. La eleccion se guarda en `localStorage`; no se solicita geolocalizacion del navegador. Las distancias son aproximadas.

El filtro lateral de resultados permite elegir una red de bibliotecas o una sucursal concreta. El selector agrupa las sucursales bajo su biblioteca matriz y se puede buscar por el nombre visible; internamente envia un codigo estable (`b:` para red, `s:` para sucursal). Las URLs antiguas con el nombre de la red siguen funcionando, y un nombre de sucursal tambien se acepta como fallback. Tras cambiar los campos de indice hay que ejecutar `make index`.

Los 304 codigos postales de la provincia de Madrid se generan con:

```bash
python3 scripts/generate_codigos_postales.py
python3 -c "import json; d=json.load(open('apps/web/lib/codigos-postales-madrid.json')); print(len(d['codigos']))"
```

## Concurrencia del worker

El worker puede ejecutar hasta 5 tareas compatibles a la vez. El numero se configura con `MEDIATECA_WORKER_CONCURRENCY` (1-5), con `python -m mediateca worker --concurrency N` o desde `Configuracion` del dashboard. El valor guardado en el dashboard prevalece sobre el entorno y se aplica al reiniciar el worker.

Nunca se ejecutan dos trabajos del mismo tipo ni combinaciones con dependencia: `discover`/`enrich`, `enrich`/`tmdb`, `enrich`/`index` y `tmdb`/`index`. `branches` es compatible con todos. Si un trabajo incompatible esta activo, el nuevo queda `pending` y espera; no se rechaza. El reclamo se serializa en PostgreSQL con `pg_advisory_xact_lock`, de modo que dos contenedores worker tampoco pueden saltarse estas reglas.

## Imagenes

| Imagen | Servicios |
|---|---|
| `mediateca-batch` | `init`, `worker`, `dashboard`, `scheduler` |
| `mediateca-web` | `api`, `web` |

Para incrementar la version, reconstruir las dos imagenes y publicarlas en una
sola orden:

```bash
make bump-release type=fix    # tambien type=major o type=minor
```

El script `scripts/bump-release.sh` actualiza `VERSION`, los `pyproject.toml`, los
`__version__` y el `package.json`, reconstruye `mediateca-batch` y
`mediateca-web`, y las publica con la etiqueta de version y `latest`. Por defecto
usa el registro `192.168.1.168:5000`; se puede cambiar con `REGISTRY`. Para
reconstruir sin cache, añade `--no-cache`:

```bash
REGISTRY=otro.registro:5000 ./scripts/bump-release.sh minor --no-cache
```

Los pasos siguen disponibles por separado con `make bump type=...` y
`make release`.

## Despliegue

- Local: `docker-compose.yml`.
- Portainer: `deploy/portainer-stack.yml`.

El stack de Portainer usa:

```text
${MEDIATECA_REGISTRY}/mediateca-batch:${MEDIATECA_IMAGE_TAG}
${MEDIATECA_REGISTRY}/mediateca-web:${MEDIATECA_IMAGE_TAG}
```

La base de datos y el indice se comparten entre todos los servicios. La ingesta es la unica propietaria de las migraciones y de las escrituras del catalogo; la API solo lee el catalogo y escribe las listas de favoritos; el portal no accede directamente a la base.

## Gestion de modelos

Los modelos SQLAlchemy, los esquemas Pydantic y `SCHEMA_VERSION` viven en `packages/shared`. API e ingesta instalan ese paquete local durante el build y no existen copias locales ni wheels versionados.

Cuando cambie el modelo:

1. Edita `packages/shared` y la migracion correspondiente en `services/enrich/scripts`.
2. Sube `SCHEMA_VERSION` si el cambio afecta al esquema.
3. Reconstruye las dos imagenes con `make release` o `make build`.
4. Despliega: `init` aplica las migraciones antes de arrancar la API.

## API

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/health` | Estado de PostgreSQL y Meilisearch |
| GET | `/api/search` | Busqueda con `q`, `soporte`, `genero`, `anio_desde`, `anio_hasta`, `idioma`, `paises_origen`, `biblioteca`, `page`, `limit`, `sort` |
| GET | `/api/records/{record_id}` | Ficha completa con fuente, ejemplares, paises de origen y `ubicacion` por ejemplar; un `TITN` suelto se resuelve como Madrid |
| GET | `/api/libraries` | Bibliotecas con numero de ejemplares |
| GET | `/api/stats` | Totales y reparto por soporte |
| POST | `/api/lists` | Crea una lista de favoritos y devuelve su token |
| GET | `/api/lists/{token}` | Lista con sus titulos y el estado de cada ficha |
| POST | `/api/lists/{token}/items` | Anade una edicion a la lista (idempotente) |
| DELETE | `/api/lists/{token}/items/{record_id}` | Quita una edicion de la lista; acepta tambien un `TITN` suelto |
| PATCH | `/api/lists/{token}` | Renombra la lista |

```bash
curl "http://localhost:8000/api/search?q=abejas&soporte=DVD&soporte=Blu-ray"
curl "http://localhost:8000/api/records/madrid:2101557"
curl "http://localhost:8000/api/records/2101557"
```

La ficha devuelve `record_id`, `fuente` y `fuente_nombre`. La identidad global es `<fuente>:<titn>`; la compatibilidad con `TITN` suelto se mantiene resolviendo a `madrid:<titn>`.

Cada ejemplar de `/api/records/{record_id}` puede incluir:

```json
"ubicacion": {
  "codigo_postal": "28801",
  "municipio": "Alcalá de Henares",
  "latitud": 40.480773,
  "longitud": -3.362149
}
```

Si la sucursal no tiene coordenadas pero tiene codigo postal, `latitud` y `longitud` son `null`; el portal resuelve el centroide del codigo postal. Si no hay datos de ubicacion, `ubicacion` es `null`.

## Fuentes y reindexado

Las fuentes OPAC viven en la tabla `fuentes`. Madrid se siembra con `MEDIATECA_OPAC_BASE_URL` y `MEDIATECA_OPAC_PATH`; Andalucía se crea con `services/enrich/scripts/migrate_andalucia.sql` y su perfil AbsysNet (`abnetcl.cgi`, `select03=05`). Cada fuente mantiene su perfil, su sesion y sus contadores. Las ediciones se identifican por `record_id` y el indice usa ese identificador.

Tras aplicar la migracion de identidad (`SCHEMA_VERSION=7`) hay que reconstruir el indice:

```bash
make migrate
make index-reset
```

Primera recolección de Andalucía:

```bash
make migrate
make harvest fuente=andalucia q=cine pages=1 limit=5
docker compose run --rm worker python -m mediateca discover --fuente andalucia --max-pages 1 --limit 20
docker compose run --rm worker python -m mediateca enrich --fuente andalucia --limit 20
docker compose run --rm worker python -m mediateca index --fuente andalucia
```

En un despliegue normal el servicio `init` detecta el salto de version y ejecuta el reindexado con `--reset`.

## Contratos

La API genera `contracts/openapi.json`. El portal genera `apps/web/lib/api-types.ts` desde ese contrato:

```bash
make openapi
make web-types
```

## Listas de favoritos

Cualquier visitante puede guardar ediciones en una lista sin crear una cuenta. La lista se guarda en PostgreSQL y se identifica por un token opaco que viaja en la URL `/lista/{token}`.

- El primer corazon crea la lista y el portal recuerda cual es la lista activa en una cookie.
- Compartir la lista es enviar ese enlace. Cualquiera que lo abra puede leerla y editarla.
- El token se guarda hasheado en la base de datos y la API lo enmascara en sus logs de acceso. Un proxy inverso debería aplicar la misma redacción.
- Las listas sin ediciones durante 180 dias se eliminan desde el servicio `init`.
- No hay cuentas, correo, contrasenas ni datos personales asociados.

## Datos y atribucion

- La fuente es el catalogo publico de AbsysNet. La recoleccion se ejecuta en `services/enrich`.
- Las direcciones, codigos postales y coordenadas de sucursal proceden del Directorio de Bibliotecas de la Comunidad de Madrid.
- Los centroides de codigos postales proceden de `kodens-dev/Spain-Postal-Codes` (MIT) y los municipios del INE via `regi-es/ds-codigos-postales-ine-es` (CC BY 4.0). La ficha muestra esta atribucion.
- No se almacenan datos personales, solo metadatos bibliograficos y de ejemplares. La ubicacion elegida por el usuario se guarda solo en su navegador (`localStorage`). Las listas de favoritos guardan solo identificadores de ediciones, un titulo opcional y marcas de tiempo.
- Las portadas, sinopsis y enlaces externos de TMDB pertenecen a sus respectivos titulares.
- Este producto usa la API de TMDB, pero no esta avalado ni certificado por TMDB.

## Licencia

Este proyecto se distribuye bajo la **PolyForm Noncommercial License 1.0.0**. Puedes usar, copiar, modificar y distribuir el software **para fines no comerciales**, manteniendo el aviso de copyright, el texto de la licencia y el credito al proyecto original. Consulta [`LICENSE`](LICENSE).

No esta permitido vender el codigo, usarlo con fines comerciales ni sublicenciarlo comercialmente. La licencia no cubre los metadatos del catalogo ni contenidos de terceros.

### Creditos

- Proyecto original: [Mediateca Madrid](https://github.com/Jesuslconde/mediateca-madrid), creado por [Jesuslconde](https://github.com/Jesuslconde).
- Los metadatos del catalogo proceden de las Bibliotecas de la Comunidad de Madrid y no estan cubiertos por esta licencia.
