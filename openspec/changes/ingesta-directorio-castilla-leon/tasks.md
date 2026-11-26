# Tasks

## 1. Búsqueda de datos

- [ ] 1.1 Localizar y verificar el directorio de Castilla y León: tipo, URL, formato y campos. Punto de partida: `datosabiertos.jcyl.es`, «Registro de instituciones bibliotecarias» (`.../instituciones_bibliotecarias/1284303481710.json`, CSV/XLS) y «paradas de bibliobuses» (`.../puntos_servicio_movil/1284294538460`).

## 2. Obtención

- [ ] 2.1 Descargar el recurso JSON/CSV y guardar una copia del fichero fuente en el entorno de trabajo.

## 3. Preparación

- [ ] 3.1 Normalizar los datos a un formato de carga (CSV/JSON/SQL) con columnas: `fuente`, `codigo_biblioteca`, `codigo_sucursal`, `nombre`, `direccion`, `municipio`, `codigo_postal`, `latitud`, `longitud`.
- [ ] 3.2 Generar un script SQL idempotente (o equivalente) que inserte/actualice `bibliotecas` y `sucursales` por `(fuente, codigo)`, sin tocar otras fuentes.

## 4. Carga y verificación

- [ ] 4.1 Ejecutar la carga en el entorno de datos y registrar el resumen.
- [ ] 4.2 Verificar idempotencia (reejecutar sin duplicados) y que no se crean ediciones ni ejemplares.

## Workflow follow-up

- Archivar el cambio tras validar la carga.
