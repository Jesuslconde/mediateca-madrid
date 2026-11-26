# Proposal

## Why

Las sucursales de la fuente `murcia` (Red de Bibliotecas Públicas de la Región de Murcia) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Murcia.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `murcia`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: directorio de la Biblioteca Regional de Murcia (`bibliotecaregional.carm.es/red-de-bibliotecas/directorio`, con perfil por biblioteca) y PDF; la URL del listado ha devuelto 404 recientemente, así que conviene verificar el acceso actual.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `murcia`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
