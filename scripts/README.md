# Scripts de mantenimiento

Esta carpeta contiene utilidades transversales del monorepo: exportación del contrato HTTP, generación del catálogo de códigos postales y publicación de versiones e imágenes.

## `export-openapi.sh`

Exporta el esquema OpenAPI de la API FastAPI:

```bash
./scripts/export-openapi.sh
# o
make openapi
```

El script:

1. Se coloca en la raíz del repositorio.
2. Crea `contracts/` si no existe.
3. Ejecuta `services/api/scripts/export_openapi.py` dentro del servicio `api`.
4. Redirige la salida a `contracts/openapi.json`.

No edita `contracts/openapi.json` manualmente. Después de regenerar el contrato se actualizan los tipos del portal:

```bash
make web-types
# o ambos pasos
make contracts
```

## `generate_codigos_postales.py`

Genera `apps/web/lib/codigos-postales-madrid.json`, utilizado por el portal como respaldo cuando una sucursal tiene código postal pero no coordenadas.

Fuentes:

- Centroides: [`kodens-dev/Spain-Postal-Codes`](https://github.com/kodens-dev/Spain-Postal-Codes), MIT.
- Municipios: INE mediante [`regi-es/ds-codigos-postales-ine-es`](https://github.com/regi-es/ds-codigos-postales-ine-es), CC BY 4.0.

Ejecución:

```bash
python3 scripts/generate_codigos_postales.py
python3 -c "import json; d=json.load(open('apps/web/lib/codigos-postales-madrid.json')); print(len(d['codigos']))"
```

El script descarga ambos CSV con un timeout de 60 segundos, filtra códigos que comienzan por `28`, normaliza el código a cinco dígitos, elimina duplicados, convierte las coordenadas a `float` y ordena por código.

Estructura de salida:

```json
{
  "fuente": "Centroides: ...; municipios: ...",
  "licencia": "MIT / CC BY 4.0",
  "codigos": [
    {
      "codigo": "28001",
      "municipio": "Madrid",
      "latitud": 40.4,
      "longitud": -3.7
    }
  ]
}
```

La atribución se guarda dentro del JSON y también se muestra en el portal.

## `bump-version.sh`

Incrementa la versión semántica centralizada en `VERSION`:

```bash
./scripts/bump-version.sh minor
# o
make bump type=minor
```

Tipos aceptados: `major`, `minor`, `fix` y el alias histórico `normal` para `major`.

Actualiza de forma coordinada:

- `VERSION`.
- `packages/shared/pyproject.toml`.
- `services/api/pyproject.toml`.
- `services/enrich/pyproject.toml`.
- `packages/shared/src/mediateca_shared/__init__.py`.
- `services/api/src/mediateca/__init__.py`.
- `services/enrich/src/mediateca/__init__.py`.
- `apps/web/package.json` y `package-lock.json` mediante `npm version --no-git-tag-version`.
- Si npm no está instalado, los dos archivos del portal se actualizan directamente sin modificar dependencias.

El script no crea commits ni tags Git.

## `release.sh`

Construye y publica las dos imágenes con la versión actual:

```bash
./scripts/release.sh
# o
make release
```

Variables:

| Variable | Predeterminado |
|---|---|
| `REGISTRY` | `192.168.1.169:5000` |
| `BATCH_IMAGE` | `mediateca-batch` |
| `WEB_IMAGE` | `mediateca-web` |
| `NO_CACHE` | `0` |
| `CONTAINER_ENGINE` | `docker` si existe; si no, `podman` |

El motor también se puede fijar explícitamente, por ejemplo `CONTAINER_ENGINE=podman ./scripts/release.sh`.

Para cada imagen publica dos etiquetas:

```text
${REGISTRY}/${BATCH_IMAGE}:${VERSION}
${REGISTRY}/${BATCH_IMAGE}:latest
${REGISTRY}/${WEB_IMAGE}:${VERSION}
${REGISTRY}/${WEB_IMAGE}:latest
```

## `bump-release.sh`

Combina incremento de versión y publicación:

```bash
./scripts/bump-release.sh fix
./scripts/bump-release.sh minor --no-cache
# o
make bump-release type=fix
```

Internamente ejecuta `bump-version.sh` y después `release.sh`. La opción `--no-cache` se transmite a la construcción de ambas imágenes.

## Buenas prácticas

- Revisa el diff de versión antes de publicar.
- No publiques solo una de las dos imágenes.
- Usa una etiqueta de versión explícita en Portainer para poder reproducir un despliegue.
- Regenera OpenAPI y los tipos TypeScript cuando cambie la API.
- Ejecuta las pruebas y la validación de migraciones antes de un release.

Más detalles operativos en [`docs/OPERATIONS.md`](../docs/OPERATIONS.md).
