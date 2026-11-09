# Proposal

## Why

El estado de préstamo por ejemplar caduca en cuanto se consulta y obliga a mantener un refresco periódico costoso que nunca refleja la realidad en tiempo real. Para el portal es más útil y honesto saber qué bibliotecas tienen el título y remitir a la ficha oficial del OPAC para el estado de préstamo actual.

## What Changes

- **BREAKING** Se elimina el concepto de disponibilidad de préstamo del modelo: campos `disponible` en edición y ejemplar, `estado` de préstamo e historial de disponibilidad.
- Al crear o actualizar la ficha de un activo se guarda únicamente la lista de bibliotecas y sucursales que poseen ejemplares, junto con su signatura, tipo y soporte.
- **BREAKING** Se elimina el refresco periódico de disponibilidad (`refresh-availability`, job del scheduler y variable `MEDIATECA_SCHEDULER_AVAILABILITY_HOURS`).
- **BREAKING** Se elimina el filtro y la faceta `disponible` de la búsqueda, la API y el portal.
- La ficha del portal muestra las bibliotecas que tienen el título y enlaza cada una a la ficha original del OPAC (`source_url`) para consultar el préstamo real.
- Se mantiene la recolección periódica de fichas para actualizar metadatos y la lista de bibliotecas, sin comprobar préstamos.

## Capabilities

### New Capabilities

<!-- Ninguna: el cambio modifica capacidades existentes. -->

### Modified Capabilities

- `modelo-catalogo`: se sustituye el requisito de ejemplares y disponibilidad por el de tenencia por biblioteca, sin estado de préstamo ni historial.
- `ingesta-catalogo`: la recolección actualiza metadatos y lista de bibliotecas, pero no refresca disponibilidad de préstamo.
- `busqueda-facetas`: se elimina el campo, la faceta y el filtro de disponibilidad del documento y de la búsqueda.
- `api-portal`: la ficha devuelve bibliotecas tenedoras y un enlace al OPAC; se retira `disponible` de las respuestas y del filtrado.
- `portal-web`: la sección de disponibilidad pasa a listar bibliotecas con enlace a la ficha del OPAC y desaparece el filtro «Solo disponible».

## Impact

- Modelo y migración: tablas `ejemplares` (quitar `estado`, `disponible`), `ediciones.disponible` e `historial_disponibilidad` (eliminar); ajustar `Biblioteca`/ejemplares a la lista de tenencia.
- Backend: `catalog/models.py`, `catalog/parser.py`, `catalog/repository.py`, `catalog/indexer.py`, `api/serializers.py`, `api/schemas.py`, `api/routers/search.py`, `api/routers/libraries.py`, `cli.py`, `core/config.py`.
- Infraestructura: `docker-compose.yml`, `.env.example`, `Makefile`, `README.md`, `docs/ARCHITECTURE.md` (retirar el job y la variable de disponibilidad).
- Frontend: `components/AvailabilityTable.tsx`, `components/FacetFilters.tsx`, `components/RecordCard.tsx`, `app/registro/[titn]/page.tsx`, `lib/api.ts`.
- Pruebas: fixtures y tests de parser que hoy afirman `disponible`/`estado`.
- **BREAKING** para clientes de la API que consuman `disponible`, `estado` o `historial`.
