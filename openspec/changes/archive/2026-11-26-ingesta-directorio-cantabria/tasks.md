# Tasks

## 1. Búsqueda de datos

- [x] 1.1 Localizar y verificar el directorio de Cantabria: tipo, URL, formato y campos. Punto de partida: descarga JSON del Directorio de Bibliotecas Españolas (DIMBE, `directoriobibliotecas.mcu.es/dimbe.cmd`), con dirección, código postal y coordenadas, y árbol `subcat` del OPAC del SLPC (`slpc.cantabria.es`), con los códigos `SUBC` de bibliotecas y sucursales.

## 2. Obtención

- [x] 2.1 Descargar/exportar el listado de bibliotecas de Cantabria y guardar una copia del fichero fuente en el entorno de trabajo.

## 3. Preparación

- [x] 3.1 Normalizar los datos a un formato de carga (CSV/JSON/SQL) con columnas: `fuente`, `codigo_biblioteca`, `codigo_sucursal`, `nombre`, `direccion`, `municipio`, `codigo_postal`, `latitud`, `longitud`.
- [x] 3.2 Generar una migración SQL idempotente (`services/enrich/scripts/migrate_sucursales_directorio_cantabria.sql`) que inserte/actualice `bibliotecas` y `sucursales` por `(fuente, codigo)` usando el árbol `subcat` del OPAC, y se aplique al iniciar la aplicación, sin tocar otras fuentes.

## 4. Carga y verificación

- [x] 4.1 Aplicar la migración al iniciar la aplicación y registrar el resumen, comprobando una instalación desde cero y una actualización.
- [x] 4.2 Verificar idempotencia (reejecutar la inicialización sin duplicados) y que no se crean ediciones ni ejemplares.

## Workflow follow-up

- Archivar el cambio tras validar la carga.
