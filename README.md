# Mediateca Madrid

Portal alternativo de búsqueda de vídeos, DVD y Blu-ray de las bibliotecas públicas de la Comunidad de Madrid.

Este repositorio contiene la **API de solo lectura y el portal**. La ingesta, el descubrimiento, el enriquecimiento y la escritura del índice viven en `mediateca-madrid-enrich`; los modelos y contratos compartidos, en `mediateca-madrid-shared`.

## Repositorios

| Repositorio | Responsabilidad |
|---|---|
| `mediateca-madrid` | API FastAPI, portal Next.js y lectura de PostgreSQL/Meilisearch |
| `mediateca-madrid-enrich` | Ingesta, worker, scheduler, migraciones y escritura del catálogo |
| `mediateca-madrid-shared` | Modelos SQLAlchemy, esquemas Pydantic y contratos OpenAPI/JSON |

## Inicio rápido

Los servicios de PostgreSQL y Meilisearch los despliega `mediateca-madrid-enrich`. Arranca primero ese proyecto y después este:

```bash
# En mediateca-madrid-enrich
make up
make migrate
make init

# En mediateca-madrid
cp .env.example .env
make up
```

Abre:

- Portal: <http://localhost:3000>
- API: <http://localhost:8000/docs>
- Meilisearch: <http://localhost:7700>

La app no ejecuta ingesta ni crea el esquema. Al arrancar comprueba que la versión del esquema compartido (`schema_meta`) coincide con la esperada.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado de PostgreSQL y Meilisearch |
| GET | `/api/search` | Búsqueda con `q`, `soporte`, `genero`, `anio_desde`, `anio_hasta`, `idioma`, `biblioteca`, `page`, `limit`, `sort` |
| GET | `/api/records/{titn}` | Ficha completa con ejemplares |
| GET | `/api/libraries` | Bibliotecas con número de ejemplares |
| GET | `/api/stats` | Totales y reparto por soporte |

```bash
curl "http://localhost:8000/api/search?q=abejas&soporte=DVD&soporte=Blu-ray"
curl "http://localhost:8000/api/search?soporte=Blu-ray&limit=5"
curl "http://localhost:8000/api/records/2101557"
```

## Estructura

```text
backend/
  src/mediateca/
    api/          FastAPI, routers, schemas y serializers
    catalog/      adaptador de búsqueda de solo lectura
    core/         configuración, base de datos, logging y cliente Meilisearch
  tests/          pytest
frontend/
  app/            páginas Next.js (inicio, búsqueda, ficha)
  components/     buscador, tarjetas, facetas, bibliotecas
  lib/            cliente de la API y tipos generados
openspec/         especificaciones y cambios
docs/             arquitectura
```

## Contratos compartidos

La app fija una versión de `mediateca-shared` y consume sus modelos y esquemas. El contrato OpenAPI se publica desde `mediateca-madrid-shared` y el portal genera sus tipos TypeScript desde ese artefacto.

## Datos y limitaciones

- La fuente es el catálogo público de AbsysNet. La recolección se ejecuta en `mediateca-madrid-enrich`.
- La ficha muestra las bibliotecas que poseen cada título y enlaza al OPAC para consultar el estado de préstamo.
- No se almacenan datos personales, solo metadatos bibliográficos y de ejemplares.
- Antes de publicar un portal en producción, revisa las condiciones de reutilización de los metadatos y atribuye la fuente.

## OpenSpec

Las especificaciones de lectura viven aquí; la planificación de ingesta se migró a `mediateca-madrid-enrich`.

```bash
openspec list --specs
openspec show portal-web
openspec show api-portal
openspec view
```

## Licencia

Este proyecto se distribuye bajo la **PolyForm Noncommercial License 1.0.0**. Puedes usar, copiar, modificar y distribuir el software **para fines no comerciales**, siempre que mantengas el aviso de copyright, el texto de la licencia y des crédito al proyecto original. Consulta [`LICENSE`](LICENSE).

No está permitido vender el código, usarlo con fines comerciales ni sublicenciarlo comercialmente. Cualquier distribución debe ser gratuita y acompañarse de esta misma licencia. La licencia no cubre los metadatos del catálogo ni contenidos de terceros.

**Nota:** por esta restricción comercial, esta licencia es *source-available* y no cumple la definición de open source de la OSI.

### Créditos

- Proyecto original: [Mediateca Madrid](https://github.com/Jesuslconde/mediateca-madrid), creado por [Jesuslconde](https://github.com/Jesuslconde).
- Los metadatos del catálogo proceden de las Bibliotecas de la Comunidad de Madrid y no están cubiertos por esta licencia.
- Las portadas, sinopsis, enlaces externos y demás contenidos de terceros pertenecen a sus respectivos titulares.

## Roadmap

Consulta [`ROADMAP.md`](ROADMAP.md).
