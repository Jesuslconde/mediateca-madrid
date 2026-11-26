# Design

## Context

La búsqueda actual filtra por una única biblioteca o sucursal mediante el parámetro `biblioteca`, que se traduce a `ubicaciones = <código>` o a coincidencias por nombre en Meilisearch. El índice no contiene coordenadas: por edición guarda `bibliotecas` (nombres de red), `ubicaciones` (códigos `b:<fuente>:<biblioteca>` y `s:<fuente>:<sucursal>`) y `ubicaciones_texto`. Las coordenadas viven en la base de datos (`sucursales`, `bibliotecas`) y los centroides de código postal, hoy solo de Madrid, en un JSON del portal.

La ficha de registro ya ordena por cercanía en cliente usando `geo.ts`, el JSON de CP y la `ubicacion` de cada ejemplar. Este cambio lleva la cercanía a la búsqueda, resuelta en el servidor. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**

- Acotar la búsqueda por radio a partir de un código postal, resuelto en el servidor y con URLs limpias (`?cp=28015&radio_km=5`).
- Permitir excluir ubicaciones del conjunto cercano y buscar solo en una concreta.
- Mantener Meilisearch y el índice sin cambios; la proximidad se traduce a filtros por códigos de ubicación ya existentes.
- Exponer coordenadas y distancia en `/api/locations` para el picker.

**Non-Goals:**

- Ordenar resultados por distancia (solo se limita).
- Geocodificar direcciones, usar geolocalización del navegador o calcular rutas.
- Cambiar el esquema de base de datos (no hay tabla nueva ni `SCHEMA_VERSION` nuevo).
- Dotar de directorio a las fuentes AbsysNet sin coordenadas: eso es `ingesta-directorios-autonomicos`, que debe ir antes.

## Decisions

### 1. Resolución de proximidad en el servidor (API)

La API resuelve `cp` + `radio_km` a un conjunto de códigos de sucursal dentro del radio y construye el filtro `ubicaciones IN [...]`. La URL queda limpia y las facetas y totales se calculan sobre el conjunto acotado sin post-procesado por ejemplar.

Alternativas descartadas: resolver en el portal (obligaría a enviar listas de códigos por URL y duplicar la lógica de distancia) y filtrar por un `cp` sin resolver en la API (no aporta la referencia).

### 2. Centroides de código postal de toda España como dato compartido

Se amplía `scripts/generate_codigos_postales.py` para dejar de filtrar por `28` y generar el JSON completo de España en `packages/shared` (dato empaquetado con el paquete Python). Un módulo de `packages/shared` lo carga y resuelve código postal → centroide. El portal consume el mismo JSON para el autocompletado del selector global.

Alternativas descartadas: tabla `codigos_postales` en base de datos (sobrecoste para un dato estático y de un solo propósito) y JSON duplicado en api y web (deriva entre copias). La forma exacta de servir el JSON al portal (alias de import o copia generada) se decide en la implementación; el dato canónico es único.

### 3. Haversine pura en Python, sin dependencia nueva

`packages/shared` incorpora `haversine_km` en Python, espejo del `geo.ts` existente. El portal conserva su copia TypeScript para la ficha de registro, que ya calcula en cliente con la `ubicacion` por ejemplar.

Alternativa descartada: dependencia geográfica externa (innecesaria para una fórmula de una línea).

### 4. Conjunto cercano solo con sucursales (y bibliotecas sin sucursales)

El conjunto permitido se compone de `s:<fuente>:<código>` de cada sucursal dentro del radio y de `b:<fuente>:<código>` únicamente de bibliotecas que no tienen sucursales. Así se evita que el código de red `b:` de una biblioteca con sucursales "readmita" ejemplares de sucursales lejanas (el índice etiqueta cada ejemplar con su red y su sucursal). La ubicación de una sucursal es su coordenada o el centroide de su CP; la de una biblioteca sin sucursales, su propio punto.

Alternativa descartada: incluir siempre los códigos `b:` en el conjunto cercano (filtra mal por red y rompe el radio).

### 5. Exclusión por sustracción del conjunto, sin post-procesado

`excluir` quita códigos del conjunto cercano antes de construir `ubicaciones IN (S − excluidos)`. Excluir una red (`b:`) elimina los `s:` de todas sus sucursales. Como el filtro es de pertenencia, una obra con ejemplares en una sucursal excluida y en otra no excluida sigue apareciendo; solo se ocultan las que no tienen ejemplares fuera de lo excluido.

Alternativa descartada: `ubicaciones NOT IN [...]` en el índice (sobre-oculta obras disponibles en varias sucursales y complica los totales).

### 6. Agregación por obra con el conjunto permitido

`aggregate_hits_by_obra` pasa de recibir una única `biblioteca` a recibir el conjunto de códigos permitidos, y recalcula ediciones, ejemplares, bibliotecas y soportes contando solo los ejemplares en ese conjunto. Sin esto, las tarjetas mostrarían bibliotecas y ejemplares fuera del radio.

Alternativa descartada: dejar la agregación sin filtrar (contadores incoherentes con el radio).

### 7. `/api/locations` expone coordenadas y distancia

`LocationOut` añade `codigo_postal`, `latitud`, `longitud` y, cuando se pide `cp` + `radio_km`, `distancia_km`. El endpoint reutiliza la misma resolución de proximidad que la búsqueda y devuelve solo las ubicaciones cercanas ordenadas por distancia. Sirve de picker de "bibliotecas resultantes".

Alternativa descartada: endpoint nuevo `/api/locations/cercanas` (redundante; extender el existente es compatible hacia atrás).

### 8. Selector global de código postal con autocompletado y persistencia

Un selector en la cabecera permite elegir CP de toda España por código o municipio (autocompletado sobre el JSON). Se guarda en `localStorage` (`mediateca:codigo-postal`, clave ya usada por la ficha) y se refleja en la URL de búsqueda (`cp`). En `/buscar`, el `cp` de la URL manda sobre `localStorage`. El radio (`radio_km`) vive solo en la URL. La ficha de registro reutiliza el mismo control, sustituyendo su `<select>` de 304 CP por el autocompletado de toda España.

Alternativas descartadas: `<select>` con miles de CP (inutilizable) y geolocalización del navegador (HTTP sin contexto seguro).

### 9. Control de radio con presets

El radio usa presets fijos (1, 2, 5, 10, 20, 50 km) más "sin límite", en lugar de un slider continuo. Los presets son suficientes para elegir biblioteca y mantienen la URL corta.

Alternativa descartada: slider continuo (más superficie de UI sin beneficio claro para este caso).

## Risks / Trade-offs

- **Cobertura desigual de coordenadas** → el radio solo localiza sucursales con coordenadas o CP; el resto queda fuera del conjunto cercano. La degradación es limpia (ver specs de `proximidad`) y depende de `ingesta-directorios-autonomicos`.
- **Centroide de CP impreciso** → la distancia es aproximada y en línea recta; se etiqueta como tal y no se promete ruta.
- **JSON de CP grande** → unos 11.000 CP es un dato estático pequeño en bytes; se versiona y se regenera con el script.
- **`excluir` sin proximidad** → sin `cp` + `radio_km`, `excluir` no tiene efecto; se documenta en la API.
- **Contadores por obra** → si la agregación no recibe el conjunto permitido, los contadores quedan incoherentes; se cubre con pruebas de la agregación con y sin radio.

## Migration Plan

1. Ampliar `scripts/generate_codigos_postales.py` (sin filtro `28`) y regenerar el JSON de toda España en `packages/shared`.
2. Añadir en `packages/shared` el cargador de centroides y `haversine_km`, con pruebas.
3. En `services/api`: módulo de resolución de proximidad, parámetros `cp`/`radio_km`/`excluir` en búsqueda, extensión de `aggregate_hits_by_obra` y de `/api/locations`, con pruebas.
4. En `apps/web`: selector global, control de radio y picker de incluir/excluir; reutilizar `geo.ts` y el JSON.
5. Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts`.
6. Ejecutar `make test`, `make lint` y `npm run build`.

No hay migración de esquema ni `SCHEMA_VERSION` nuevo. Rollback: los parámetros y campos son aditivos; los clientes anteriores los ignoran y revertir las imágenes devuelve el comportamiento previo.

## Open Questions

- Valor exacto de los presets de radio (se asume 1/2/5/10/20/50 km) — no cambia specs ni tareas.
- Mecanismo concreto de importación del JSON en el portal (alias vs copia generada) — decisión de implementación.
