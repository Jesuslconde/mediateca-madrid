# Proposal

## Why

Las sucursales de la fuente `aragon` (Red de Bibliotecas de Aragón) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio de bibliotecas mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Aragón.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `aragon`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: datos abiertos de Aragón Open Data (`opendata.aragon.es`), recursos «Bibliotecas» (`resource_id=282`) y «Sucursales» (`resource_id=283`), en JSON, con códigos `bicobi`/`bicobg` y `sucobi`/`sucosu`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `aragon`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
