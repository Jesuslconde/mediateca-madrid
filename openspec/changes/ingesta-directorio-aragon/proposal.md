# Proposal

## Why

Las sucursales de la fuente `aragon` (Red de Bibliotecas de Aragón) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio de bibliotecas mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de Aragón.
- Generar una carga idempotente (script SQL o datos preparados) para `bibliotecas` y `sucursales` de la fuente `aragon`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: datos abiertos de Aragón Open Data (`opendata.aragon.es`), recursos «Bibliotecas» (`resource_id=282`) y «Sucursales» (`resource_id=283`), en JSON, con códigos `bicobi`/`bicobg` y `sucobi`/`sucosu`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `aragon`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
