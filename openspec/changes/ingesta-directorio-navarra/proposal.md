# Proposal

## Why

Las sucursales de la fuente `navarra` (Red de Bibliotecas Públicas de Navarra) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Navarra.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `navarra`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: datos abiertos de Navarra (`datosabiertos.navarra.es`), recurso «Bibliotecas públicas» (`.../datastore/dump/8b7cd771-7918-4a4b-a75c-f9f9f6677056?format=json`), con `Denominacion`, `Direccion`, `Distrito Postal` y `Localidad` (sin código ni coordenadas).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `navarra`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
