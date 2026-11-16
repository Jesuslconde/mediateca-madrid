# Proposal

## Why

La ficha de un registro lista las bibliotecas que tienen ejemplares en orden alfabético, sin indicar cuáles están más cerca de la persona que consulta. En un catálogo con decenas de sucursales, eso obliga a comparar municipios y direcciones a mano para decidir a qué biblioteca ir.

La ordenación por cercanía se hará con un código postal elegido manualmente, no con geolocalización del navegador: el despliegue actual es HTTP y la geolocalización requiere un contexto seguro; además, así no se recoge ni se envía la ubicación precisa de nadie.

## What Changes

- Se añade la tabla `sucursales` con código, biblioteca, nombre, municipio, dirección, código postal y coordenadas.
- `Biblioteca` incorpora `codigo_postal` y se rellenan sus campos de ubicación cuando el directorio tenga una ficha de ámbito de biblioteca.
- `Ejemplar` expone una relación de solo lectura con su `Sucursal` por `sucursal_codigo`, sin clave foránea nueva ni relleno retroactivo.
- Se incorpora la ingesta del Directorio de Bibliotecas de la Comunidad de Madrid: paginación de fichas, lectura de `SUBC`, dirección, código postal y coordenadas del enlace de mapa, y emparejamiento `SUBC` ↔ `bicobi`/`sucosu` del OPAC.
- Se añade el comando `mediateca refresh-branches` y el atajo `make branches` para actualizar las sucursales de forma idempotente y con un resumen de cobertura.
- La API expone `EjemplarOut.ubicacion` con código postal, municipio, latitud y longitud; si la sucursal no tiene coordenadas, se conserva el código postal para que el portal use su centroide.
- El portal convierte la tabla de bibliotecas en un componente cliente con un selector de código postal, cálculo de distancia Haversine, distancias aproximadas y orden alfabético por defecto. La elección se recuerda en `localStorage`.
- Se añade un JSON estático con los 304 códigos postales de la provincia de Madrid, generado a partir de centroides abiertos y del municipio del INE.
- Se incrementa `SCHEMA_VERSION` a `5` y se añade la migración idempotente correspondiente.

Queda fuera de alcance la geolocalización del navegador, la geocodificación de direcciones en esta primera versión, los mapas y rutas, la ordenación por cercanía en la búsqueda y cualquier cambio en Meilisearch.

## Capabilities

### New Capabilities

- `directorio-bibliotecas`: ingesta y mantenimiento de las fichas de sucursal del Directorio de Bibliotecas de la Comunidad de Madrid, con emparejamiento por código, dirección, código postal y coordenadas, además del comando de actualización y su cobertura.

### Modified Capabilities

- `modelo-catalogo`: se añade la entidad de sucursal y los datos de ubicación asociados a biblioteca y ejemplar, con incremento de `SCHEMA_VERSION`.
- `api-portal`: la ficha de registro expone la ubicación disponible de cada ejemplar para permitir la ordenación por cercanía en el cliente.
- `portal-web`: la sección de bibliotecas permite ordenar por cercanía a un código postal, muestra distancias aproximadas y conserva el orden alfabético como opción por defecto.

## Impact

- `packages/shared`: modelos SQLAlchemy, esquemas Pydantic y `SCHEMA_VERSION`.
- `services/enrich`: cliente y parser del directorio, repositorio de sucursales, comando CLI, migración, fixtures y pruebas.
- `services/api`: serializador de la ficha, carga de la relación de sucursal, esquema de ubicación y pruebas.
- `apps/web`: tabla de bibliotecas como componente cliente, utilidades de distancia, JSON de códigos postales y nota de atribución.
- Contratos: `contracts/openapi.json` y `apps/web/lib/api-types.ts` regenerados.
- Operación: `Makefile`, README y documentación de arquitectura; no se modifica Meilisearch ni la búsqueda.
- Fuentes externas: Directorio de Bibliotecas de la Comunidad de Madrid y datasets abiertos de centroides de códigos postales (kodens, MIT; INE, CC BY 4.0).
