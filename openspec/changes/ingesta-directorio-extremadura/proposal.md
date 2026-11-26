# Proposal

## Why

Las sucursales de la fuente `extremadura` (Red de Bibliotecas de Extremadura) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Extremadura.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `extremadura`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: directorio en XLS y PDF de la Junta de Extremadura (`juntaex.es`, «Directorio de la Red de Bibliotecas de Extremadura»).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `extremadura`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
