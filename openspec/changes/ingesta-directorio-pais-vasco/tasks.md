# Tasks

## 1. Búsqueda de datos

- [ ] 1.1 Localizar y verificar el directorio de Euskadi: tipo, URL, formato y campos. Punto de partida: Open Data Euskadi, «Bibliotecas públicas de Euskadi» (`opendata.euskadi.eus/.../ds_localizaciones/bibliotecas_publicas_euskadi/opendata/bibliotecas.json`), con dirección, municipio, código postal y coordenadas (`latwgs84`/`lonwgs84`), sin código.

## 2. Obtención

- [ ] 2.1 Descargar el JSON y guardar una copia del fichero fuente en el entorno de trabajo.

## 3. Preparación

- [ ] 3.1 Normalizar los datos a un formato de carga (CSV/JSON/SQL) con columnas: `fuente`, `codigo_biblioteca`, `codigo_sucursal`, `nombre`, `direccion`, `municipio`, `codigo_postal`, `latitud`, `longitud`.
- [ ] 3.2 Generar un script SQL idempotente (o equivalente) que inserte/actualice `bibliotecas` y `sucursales` por nombre (al no haber código) sin tocar otras fuentes.

## 4. Carga y verificación

- [ ] 4.1 Ejecutar la carga en el entorno de datos y registrar el resumen.
- [ ] 4.2 Verificar idempotencia (reejecutar sin duplicados) y que no se crean ediciones ni ejemplares.

## Workflow follow-up

- Archivar el cambio tras validar la carga.
