# Proposal

## Why

Las sucursales de la fuente `valencia` (Red Electrónica de Lectura Pública Valenciana) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de la Comunidad Valenciana.
- Generar una carga idempotente para `bibliotecas` y `sucursales` de la fuente `valencia`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: datos abiertos de la Generalitat (`dadesobertes.gva.es`), recurso «Directorio de bibliotecas de la Comunitat Valenciana» (CSV de 2020, datos de contacto, sin geolocalización).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `valencia`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
