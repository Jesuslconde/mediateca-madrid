# Proposal

## Why

Las sucursales de la fuente `pais-vasco` (Red de Lectura Pública de Euskadi, RLPE) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una carga de datos única y manual, sin añadir código a la aplicación.

## What Changes

- Buscar, obtener, preparar y cargar manualmente el directorio de bibliotecas de Euskadi.
- Generar una carga idempotente para `bibliotecas` y `sucursales` de la fuente `pais-vasco`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: Open Data Euskadi (`opendata.euskadi.eus`), recurso «Bibliotecas públicas de Euskadi» (`.../ds_localizaciones/bibliotecas_publicas_euskadi/opendata/bibliotecas.json`), con dirección, municipio, código postal y coordenadas (`latwgs84`/`lonwgs84`), sin código (emparejamiento por nombre).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `pais-vasco`.
- Sin cambios en `services/enrich`, `services/api`, `apps/web` ni contratos.
