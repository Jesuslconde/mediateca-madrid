# Proposal

## Why

Las sucursales de la fuente `la-rioja` (Red de Lectura Pública de La Rioja) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de La Rioja.
- Generar una carga idempotente para `bibliotecas` y `sucursales` de la fuente `la-rioja`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida: el portal de dato abierto de La Rioja (`web.larioja.org/dato-abierto`, CKAN `ckan.larioja.org`) no devuelve ningún dataset con «bibliotecas»; el directorio está disponible vía web/portal de la Red de Lectura Pública.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `la-rioja`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
