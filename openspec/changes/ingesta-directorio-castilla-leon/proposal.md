# Proposal

## Why

Las sucursales de la fuente `castilla-leon` (Red de Bibliotecas de Castilla y León, RABEL) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Castilla y León.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `castilla-leon`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: datos abiertos de la Junta (`datosabiertos.jcyl.es`), «Registro de instituciones bibliotecarias» (`.../instituciones_bibliotecarias/1284303481710.json`, también CSV/XLS), y «paradas de bibliobuses» (`.../puntos_servicio_movil/1284294538460`).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `castilla-leon`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
