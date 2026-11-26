# Proposal

## Why

Las sucursales de la fuente `asturias` (Red de Bibliotecas de Asturias) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de Asturias.
- Generar una carga idempotente para `bibliotecas` y `sucursales` de la fuente `asturias`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: directorio en PDF publicado por el Principado (`absys.asturias.es/opacbp/imag/ba_directorio.pdf`), con concejo, código, denominación, dirección y contacto.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `asturias`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
