# Tasks

## 1. Búsqueda de datos

- [ ] 1.1 Localizar y verificar el directorio de Murcia: tipo, URL, formato y campos. Punto de partida: directorio de la Biblioteca Regional de Murcia (`bibliotecaregional.carm.es/red-de-bibliotecas/directorio`, perfil por biblioteca) y PDF; verificar el acceso actual (la URL del listado ha dado 404).

## 2. Obtención

- [ ] 2.1 Descargar el directorio (páginas o PDF) y guardar una copia del fichero fuente en el entorno de trabajo.

## 3. Preparación

- [ ] 3.1 Normalizar los datos a un formato de carga (CSV/JSON/SQL) con columnas: `fuente`, `codigo_biblioteca`, `codigo_sucursal`, `nombre`, `direccion`, `municipio`, `codigo_postal`, `latitud`, `longitud`.
- [ ] 3.2 Generar una migración SQL idempotente (`services/enrich/scripts/migrate_sucursales_directorio_murcia.sql`) que inserte/actualice `bibliotecas` y `sucursales` por `(fuente, codigo)` y se aplique al iniciar la aplicación, sin tocar otras fuentes.

## 4. Carga y verificación

- [ ] 4.1 Aplicar la migración al iniciar la aplicación y registrar el resumen, comprobando una instalación desde cero y una actualización.
- [ ] 4.2 Verificar idempotencia (reejecutar la inicialización sin duplicados) y que no se crean ediciones ni ejemplares.

## Workflow follow-up

- Archivar el cambio tras validar la carga.
