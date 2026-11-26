# Proposal

## Why

La búsqueda actual filtra por una única biblioteca y no tiene noción de distancia: para elegir a qué biblioteca ir hay que comparar municipios y direcciones a mano, y esto se agrava ahora que el catálogo cubre varias comunidades. El portal ya ordena por cercanía en la ficha del registro, pero la búsqueda no puede acotar "bibliotecas a menos de X km de mi código postal" ni incluir o excluir bibliotecas concretas del conjunto cercano.

## What Changes

- Se añade un **selector global de código postal** para toda España, compartido con la ficha del registro, persistido en `localStorage` y reflejado en la URL en `/buscar` (`cp`).
- Se añade un **filtro por radio de distancia** (`radio_km`), resuelto en el servidor: el CP se resuelve a su centroide y se calcula el conjunto de sucursales dentro del radio.
- Se añade un **picker de bibliotecas resultantes** con dos modos: buscar en todas excluyendo algunas (`excluir`) o buscar solo en una concreta (`biblioteca`).
- Se amplían los **centroides de código postal a toda España**, como fuente de datos compartida entre el servidor y el portal.
- El cálculo de distancia se hace en el servidor con Haversine; **no se ordenan resultados por distancia** en esta versión, solo se limita.

Queda fuera de alcance ordenar por cercanía, geocodificar direcciones, la geolocalización del navegador y cualquier mapa o cálculo de rutas.

## Capabilities

### New Capabilities

- `proximidad`: resolución de un código postal a su centroide y cálculo de distancia entre un punto de referencia y las sucursales, para determinar qué bibliotecas quedan dentro de un radio, con degradación limpia cuando una sucursal no tiene coordenadas.

### Modified Capabilities

- `busqueda-facetas`: filtro por proximidad (radio de distancia) y filtro de ubicación múltiple con inclusión y exclusión de bibliotecas.
- `api-portal`: `GET /api/search` acepta `cp`, `radio_km` y `excluir`; `GET /api/locations` expone coordenadas y distancia opcional para el picker.
- `portal-web`: selector global de código postal, control de radio y picker de incluir/excluir bibliotecas cercanas.

## Impact

- `packages/shared`: datos de centroides de CP de toda España y utilidad Haversine en Python.
- `services/api`: resolución de proximidad, construcción del filtro de búsqueda, `aggregate_hits_by_obra` con el conjunto permitido y endpoint de ubicaciones con distancia.
- `apps/web`: selector global de CP con autocompletado, control de radio, picker de bibliotecas y reutilización de `geo.ts`.
- Contratos: `contracts/openapi.json` y `apps/web/lib/api-types.ts` regenerados.
- Dependencia: el cambio `ingesta-directorios-autonomicos` debe abordarse antes, para que las sucursales de todas las comunidades tengan coordenadas.
