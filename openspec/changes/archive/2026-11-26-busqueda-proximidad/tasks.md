# Tasks

## 1. Centroides de código postal y geo en packages/shared

- [x] 1.1 Ampliar `scripts/generate_codigos_postales.py` para generar toda España (eliminar el filtro `28`) y escribir el JSON canónico en `packages/shared`. Verificar: el JSON incluye 28015 y 41001 con latitud y municipio.
- [x] 1.2 Añadir en `packages/shared` el cargador de centroides (código postal → latitud, longitud, municipio) y `haversine_km`, con pruebas de CP conocido, CP desconocido y distancia aproximada. Verificar: `make test-shared`.
- [x] 1.3 Documentar la fuente y la licencia de los centroides en el README. Verificar: el texto de atribución es visible y cita las fuentes.

## 2. Proximidad y búsqueda en services/api

- [x] 2.1 Implementar el módulo de resolución de proximidad en `services/api`: cargar sucursales y bibliotecas sin sucursales, calcular el conjunto dentro del radio y aplicar `excluir`. Verificar: pruebas unitarias de sucursal con coordenadas, con CP sin coordenadas, fuera de radio y red excluida.
- [x] 2.2 Añadir los parámetros `cp`, `radio_km` y `excluir` a `GET /api/search` y construir el filtro `ubicaciones IN [...]`. Verificar: `make test-api` con búsqueda por radio, radio sin `cp` (422) y `cp` no resoluble (422).
- [x] 2.3 Extender `aggregate_hits_by_obra` para recibir el conjunto permitido y recalcular ediciones, ejemplares, bibliotecas y soportes solo con ejemplares permitidos. Verificar: pruebas de agregación con y sin radio.
- [x] 2.4 Extender `GET /api/locations` y `LocationOut` con `codigo_postal`, `latitud`, `longitud` y `distancia_km`, y aceptar `cp` + `radio_km`. Verificar: pruebas de listado con coordenadas y de ubicaciones cercanas ordenadas por distancia.

## 3. Portal: selector global, radio y picker en apps/web

- [x] 3.1 Poner a disposición del portal el JSON de toda España (copia generada o alias) y crear el selector global de código postal con autocompletado por código o municipio en la cabecera, con persistencia en `localStorage` y reflejo en la URL. Verificar: `npm run build` y QA manual de elegir CP, recargar y compartir la URL.
- [x] 3.2 Añadir el control de radio con presets y la opción «sin límite» en la página de resultados. Verificar: `npm run build` y que la URL refleja `radio_km`.
- [x] 3.3 Añadir el picker de bibliotecas cercanas que permita marcar/desmarcar para excluir y elegir buscar solo en una. Verificar: QA manual de excluir sucursal, excluir red y buscar solo en una.
- [x] 3.4 Reutilizar el selector global en la ficha de registro (`LibrariesTable`), sustituyendo el `<select>` de 304 CP. Verificar: `npm run build` y que la ficha ordena por cercanía con CP de cualquier provincia.

## 4. Contrato e integración

- [x] 4.1 Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts` con `make contracts`. Verificar: el contrato incluye `cp`, `radio_km`, `excluir` y los nuevos campos de `LocationOut`.
- [x] 4.2 Ejecutar `make test`, `make lint` y `npm run build`. Verificar: todas las comprobaciones pasan.

## Workflow follow-up

- Aplicar antes `ingesta-directorios-autonomicos` para que las sucursales de las demás comunidades tengan coordenadas y el radio tenga cobertura completa.
- Archivar el cambio tras la revisión y la verificación.
