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
make branches
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

En la ficha de un registro se puede elegir un codigo postal para ordenar las bibliotecas por cercania. Sin seleccion, el orden es alfabetico. La eleccion se guarda en `localStorage`; no se solicita geolocalizacion del navegador. Las distancias son aproximadas.

Los 304 codigos postales de la provincia de Madrid se generan con:

```bash
python3 scripts/generate_codigos_postales.py
python3 -c "import json; d=json.load(open('apps/web/lib/codigos-postales-madrid.json')); print(len(d['codigos']))"
```

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

La base de datos y el indice se comparten entre todos los servicios. La ingesta es la unica propietaria de las migraciones y de las escrituras del catalogo; la API y el portal solo leen.

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
| GET | `/api/records/{titn}` | Ficha completa con ejemplares, paises de origen y `ubicacion` por ejemplar |
| GET | `/api/libraries` | Bibliotecas con numero de ejemplares |
| GET | `/api/stats` | Totales y reparto por soporte |

```bash
curl "http://localhost:8000/api/search?q=abejas&soporte=DVD&soporte=Blu-ray"
curl "http://localhost:8000/api/records/2101557"
```

Cada ejemplar de `/api/records/{titn}` puede incluir:

```json
"ubicacion": {
  "codigo_postal": "28801",
  "municipio": "Alcalá de Henares",
  "latitud": 40.480773,
  "longitud": -3.362149
}
```

Si la sucursal no tiene coordenadas pero tiene codigo postal, `latitud` y `longitud` son `null`; el portal resuelve el centroide del codigo postal. Si no hay datos de ubicacion, `ubicacion` es `null`.

## Contratos

La API genera `contracts/openapi.json`. El portal genera `apps/web/lib/api-types.ts` desde ese contrato:

```bash
make openapi
make web-types
```

## Datos y atribucion

- La fuente es el catalogo publico de AbsysNet. La recoleccion se ejecuta en `services/enrich`.
- Las direcciones, codigos postales y coordenadas de sucursal proceden del Directorio de Bibliotecas de la Comunidad de Madrid.
- Los centroides de codigos postales proceden de `kodens-dev/Spain-Postal-Codes` (MIT) y los municipios del INE via `regi-es/ds-codigos-postales-ine-es` (CC BY 4.0). La ficha muestra esta atribucion.
- No se almacenan datos personales, solo metadatos bibliograficos y de ejemplares. La ubicacion elegida por el usuario se guarda solo en su navegador (`localStorage`).
- Las portadas, sinopsis y enlaces externos de TMDB pertenecen a sus respectivos titulares.
- Este producto usa la API de TMDB, pero no esta avalado ni certificado por TMDB.

## Licencia

Este proyecto se distribuye bajo la **PolyForm Noncommercial License 1.0.0**. Puedes usar, copiar, modificar y distribuir el software **para fines no comerciales**, manteniendo el aviso de copyright, el texto de la licencia y el credito al proyecto original. Consulta [`LICENSE`](LICENSE).

No esta permitido vender el codigo, usarlo con fines comerciales ni sublicenciarlo comercialmente. La licencia no cubre los metadatos del catalogo ni contenidos de terceros.

### Creditos

- Proyecto original: [Mediateca Madrid](https://github.com/Jesuslconde/mediateca-madrid), creado por [Jesuslconde](https://github.com/Jesuslconde).
- Los metadatos del catalogo proceden de las Bibliotecas de la Comunidad de Madrid y no estan cubiertos por esta licencia.
