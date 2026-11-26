# Tasks

## 1. Búsqueda de datos

- [x] 1.1 Localizar y verificar el directorio de Aragón: tipo, URL, formato y campos (denominación, dirección, municipio, código postal, coordenadas y código/identidad). Punto de partida: Aragón Open Data, recursos «Bibliotecas» (`resource_id=282`) y «Sucursales» (`resource_id=283`) en `opendata.aragon.es`.

## 2. Obtención

- [x] 2.1 Descargar los recursos de bibliotecas y sucursales y guardar una copia del fichero fuente en el entorno de trabajo.

## 3. Preparación

- [x] 3.1 Normalizar los datos a un formato de carga (CSV/JSON/SQL) con columnas: `fuente`, `codigo_biblioteca`, `codigo_sucursal`, `nombre`, `direccion`, `municipio`, `codigo_postal`, `latitud`, `longitud`.
- [x] 3.2 Generar una migración SQL idempotente (`services/enrich/scripts/migrate_sucursales_directorio_aragon.sql`) que inserte/actualice `bibliotecas` y `sucursales` por `(fuente, codigo)` y se aplique al iniciar la aplicación, sin tocar otras fuentes.

## 4. Carga y verificación

- [x] 4.1 Aplicar la migración al iniciar la aplicación y registrar el resumen (bibliotecas/sucursales creadas y actualizadas, con código postal y con coordenadas), comprobando una instalación desde cero y una actualización.
- [x] 4.2 Verificar idempotencia (reejecutar la inicialización sin duplicados) y que no se crean ediciones ni ejemplares.

## Workflow follow-up

- Archivar el cambio tras validar la carga.
