# Proposal

## Why

La fuente `andalucia` ya está registrada, pero su catálogo no se puede recolectar de forma automatizada: el OPAC devuelve CAPTCHA y no expone OAI ni SRU. Mientras tanto, la Junta de Andalucía publica un directorio abierto con 1126 unidades (876 bibliotecas) que incluye dirección, código postal, coordenadas, contacto y el `SUBC` del OPAC. Hoy la tarea `branches` para Andalucía solo informa de que no hay directorio, así que el portal no tiene ubicaciones andaluzas y el catálogo no puede relacionar ejemplares con sus sucursales.

## What Changes

- Añadir un tipo de directorio `opendata` para leer `https://datos.juntadeandalucia.es/api/v0/libraries/all?format=json` como fuente de ubicaciones, sin scrapear el OPAC.
- Normalizar los campos del directorio: código postal a cadena de 5 dígitos, coordenadas con coma decimal a `float`, correos múltiples y códigos INE de municipio y localidad.
- Crear y actualizar `Biblioteca` y `Sucursal` a partir del directorio cuando la fuente no tiene inventario OPAC, de forma idempotente y sin borrar registros ausentes.
- Reutilizar el trabajo `branches` y `refresh-branches`, con una política por fuente: `match` (Madrid, solo bibliotecas conocidas) y `create` (Andalucía, el directorio puede crear bibliotecas y sucursales).
- Ingerir por defecto solo `unit_type_name = "Biblioteca"` (876), con la posibilidad de incluir centros de documentación por configuración.
- No usar coordenadas de bibliotecas móviles ni de bibliobuses, igual que en Madrid.
- Añadir una migración idempotente que declare el directorio de Andalucía en `fuentes.options` sin tocar el perfil OPAC.
- **BREAKING**: ninguna. La fuente, la identidad `record_id`, el esquema de datos, el contrato de la API y el índice no cambian.

## Capabilities

### New Capabilities

Ninguna. La ingesta del directorio encaja en la capacidad existente `directorio-bibliotecas`.

### Modified Capabilities

- `directorio-bibliotecas`: admitir un directorio servido por API de datos abiertos, normalizar sus campos y permitir que una fuente sin inventario OPAC cree bibliotecas y sucursales desde el directorio.
- `cola-trabajos`: precisar que `branches` solo actualiza bibliotecas conocidas en fuentes con política `match`, y que en fuentes con política `create` puede crear bibliotecas y sucursales desde el directorio.
- `operacion-despliegue`: añadir la migración idempotente que configura el directorio abierto de Andalucía.

## Impact

- `services/enrich/src/mediateca/catalog/directory.py`: nuevo lector `opendata`, normalización y modo de creación.
- `services/enrich/src/mediateca/catalog/repository.py`: creación de bibliotecas desde el directorio cuando no existen.
- `services/enrich/src/mediateca/cli.py` y `services/enrich/src/mediateca/catalog/jobs.py`: despacho del cliente por tipo de directorio y paso del modo de la fuente.
- `services/enrich/scripts`: nueva migración idempotente de configuración del directorio.
- `services/enrich/tests`: fixtures JSON, pruebas de normalización, creación, idempotencia, filtros y aislamiento de Madrid.
- `docs/`, `README.md` y `.env.example`: documentación del comando y de la cobertura del directorio.
- Sin cambios en `packages/shared`, `services/api`, `apps/web`, `contracts` ni en el esquema de PostgreSQL.
