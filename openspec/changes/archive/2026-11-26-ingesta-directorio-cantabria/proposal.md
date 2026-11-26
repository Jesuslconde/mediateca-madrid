# Proposal

## Why

Las sucursales de la fuente `cantabria` (Sistema de Lectura Pública de Cantabria) no tienen dirección, código postal ni coordenadas y quedan fuera del filtro por proximidad. Este cambio incorpora su directorio mediante una migración de datos idempotente que se aplica al iniciar la aplicación, sin añadir código de aplicación.

## What Changes

- Buscar, obtener, preparar y cargar mediante una migración el directorio de bibliotecas de Cantabria.
- Generar una migración idempotente para `bibliotecas` y `sucursales` de la fuente `cantabria`.
- Sin cambios de código en la aplicación ni en los contratos.

Punto de partida conocido: Directorio de Bibliotecas Españolas (DIMBE) del Ministerio de Cultura (`directoriobibliotecas.mcu.es/dimbe.cmd`), con dirección, código postal y coordenadas. El selector `subcat` del OPAC del SLPC publica además los códigos `SUBC` del árbol de bibliotecas y sucursales; se usa ese código para la identidad y DIMBE para la ubicación.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna.

## Impact

- Datos: alta/actualización de filas en `bibliotecas` y `sucursales` de la fuente `cantabria`.
- Sin cambios de código en `services/api`, `apps/web` ni contratos; la carga se añade como migración en `services/enrich/scripts`.
