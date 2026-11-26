# Proposal

## Why

Las sucursales de la fuente `murcia` (Red de Bibliotecas Públicas de la Región de Murcia) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de Murcia.
- Generar una carga idempotente para `bibliotecas` y `sucursales` de la fuente `murcia`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: directorio de la Biblioteca Regional de Murcia (`bibliotecaregional.carm.es/red-de-bibliotecas/directorio`, con perfil por biblioteca) y PDF; la URL del listado ha devuelto 404 recientemente, así que conviene verificar el acceso actual.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `murcia`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
