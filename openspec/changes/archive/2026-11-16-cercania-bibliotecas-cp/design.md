# Design

## Context

La ficha de registro se renderiza en el servidor y delega la lista de bibliotecas en `apps/web/components/LibrariesTable.tsx`, que agrupa por nombre de biblioteca y sucursal y ordena alfabéticamente. La API devuelve los ejemplares sin coordenadas. El modelo `Biblioteca` ya tiene `municipio`, `direccion`, `latitud` y `longitud`, pero la ingesta solo rellena `codigo` y `nombre`; `Ejemplar` conserva `sucursal_codigo` y `sucursal_nombre`.

El despliegue actual sirve el portal por HTTP plano, sin TLS. La geolocalización del navegador requiere un contexto seguro, así que la referencia será manual. El Directorio de Bibliotecas de la Comunidad de Madrid ofrece una ficha por sucursal con `SUBC` compatible con los códigos del OPAC y, en algunos casos, coordenadas en el enlace de mapa. Los datasets abiertos de códigos postales cubren los 304 CP de la provincia de Madrid con centroide y municipio.

Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**

- Almacenar la ubicación de cada sucursal con código postal y coordenadas cuando existan.
- Exponer una ubicación opcional por ejemplar sin romper el contrato actual.
- Permitir que el portal ordene por cercanía a un CP elegido manualmente, con orden alfabético por defecto y degradación limpia.
- Mantener la ingesta del directorio separada de la recolección del OPAC y ejecutable de forma manual e idempotente.

**Non-Goals:**

- Geocodificar direcciones en esta versión; el CP es el respaldo.
- Geolocalización del navegador, mapas, rutas o cálculo de itinerarios.
- Ordenar por cercanía los resultados de búsqueda o el filtro de biblioteca.
- Cambiar Meilisearch o el contrato de búsqueda.
- Programar automáticamente la actualización del directorio.

## Decisions

### 1. Entidad `Sucursal` en lugar de coordenadas en `Biblioteca`

Una biblioteca puede tener varias sucursales en códigos postales distintos. Guardar coordenadas solo en `Biblioteca` haría que todas las sucursales de una red compartieran punto, lo que inutiliza la ordenación dentro de Madrid. Se crea `Sucursal` con `codigo` único, `biblioteca_id`, `nombre`, `municipio`, `direccion`, `codigo_postal`, `latitud`, `longitud` y `updated_at`.

`Biblioteca` conserva sus campos de ubicación y añade `codigo_postal` para servir de respaldo en fichas de ámbito de biblioteca o ejemplares sin sucursal. No se duplican coordenadas en cada `Ejemplar`: la copia referencia la sucursal por código.

Alternativas descartadas: coordenadas en `Ejemplar` (duplicación por copia) y coordenadas solo en `Biblioteca` (precisión insuficiente).

### 2. Relación de solo lectura `Ejemplar.sucursal` por código

`Ejemplar.sucursal_codigo` ya existe. Se añade una relación viewonly con `primaryjoin="foreign(Ejemplar.sucursal_codigo) == Sucursal.codigo"`, sin clave foránea nueva ni relleno retroactivo. La API carga la relación con `selectinload` para evitar consultas por ejemplar.

Esto evita una migración de datos sobre `ejemplares` y mantiene compatibles los tests que usan una sesión falsa. Si la relación viewonly diera problemas con SQLAlchemy, la alternativa es construir un mapa `codigo -> Sucursal` en el router de records con una segunda consulta; se descarta como primera opción porque obliga a tocar los dobles de prueba de la API.

Alternativa descartada: `Ejemplar.sucursal_id` con clave foránea y backfill (más migración y riesgo para un dato derivado).

### 3. Ingesta del directorio en un módulo y comando propios

Se añade `services/enrich/src/mediateca/catalog/directory.py` con:

- Cliente `httpx` con retardo configurable y reintentos para la paginación de `registros.cmd` y las fichas `registro.cmd?id=...`.
- Parser de listado para recolectar identificadores y parser de ficha para extraer nombre, `SUBC`, biblioteca, sucursal, dirección, municipio, CP y coordenadas.
- Extracción de coordenadas solo del último `ll=` del enlace de mapa; `sll=` y `sspn=` se ignoran porque pueden ser un centro obsoleto. Los enlaces cortos y las consultas `q=` no aportan coordenadas.
- Omisión de fichas sin `SUBC`, cerradas y coordenadas de paradas de bibliobuses.

El repositorio añade `upsert_sucursal`, idempotente por código, que actualiza en su sitio y no borra sucursales ausentes. Si la ficha no aporta coordenadas, no se sobrescriben las existentes. Si el `SUBC` no tiene una biblioteca conocida, se omite y se cuenta en la cobertura.

El comando `mediateca refresh-branches` ejecuta la actualización con `--delay`, `--limit` y un resumen de fichas leídas, con `SUBC`, con CP, con coordenadas, emparejadas y omitidas. `make branches` es el atajo. No se añade job de scheduler en esta versión.

Alternativas descartadas: usar la página `SUBC` del OPAC (su `data-geoview` es el centro de Madrid por defecto), usar el dataset CKAN de bibliotecas (no tiene códigos ni coordenadas) y geocodificar en la ingesta (se pospone).

### 4. Códigos postales como JSON estático del portal

El portal necesita una referencia de CP estable y pequeña (304 filas). Se genera `apps/web/lib/codigos-postales-madrid.json` con `codigo`, `municipio`, `latitud` y `longitud`, a partir de:

- Centroides: `kodens-dev/Spain-Postal-Codes` (MIT).
- Municipio: `regi-es/ds-codigos-postales-ine-es` / INE (CC BY 4.0).

El script `scripts/generate_codigos_postales.py` descarga ambos CSV, filtra los CP que empiezan por `28`, une por CP y escribe el JSON. El JSON se versiona y se regenera solo cuando cambian las fuentes. No se crea tabla ni endpoint porque el único consumidor es el portal; si otro cliente lo necesita, se puede promover a API en un cambio posterior.

Alternativas descartadas: tabla `codigos_postales` y endpoint (sobredimensionado para 304 filas y un solo consumidor), geocodificación en tiempo de petición (dependencia externa y latencia) y derivar centroides solo de las bibliotecas (deja fuera CP sin biblioteca).

### 5. `UbicacionOut` opcional en `EjemplarOut`

Se añade a `packages/shared/src/mediateca_shared/schemas.py`:

```text
UbicacionOut:
  codigo_postal: str | None
  municipio: str | None
  latitud: float | None
  longitud: float | None
```

`EjemplarOut.ubicacion` es opcional. La resolución en `serialize_record` es:

1. Si el ejemplar tiene sucursal, usar sus campos; no sustituir por la biblioteca si la sucursal existe pero no tiene coordenadas, porque se conserva el CP para el centroide.
2. Si no hay sucursal, usar la ubicación de la biblioteca.
3. Si todos los campos son nulos, devolver `null`.

El router de records carga `Ejemplar.sucursal` con `selectinload`. El campo es opcional, por lo que clientes anteriores siguen funcionando; se regeneran `contracts/openapi.json` y `apps/web/lib/api-types.ts`.

Alternativas descartadas: ordenar en el servidor con `?lat=&lon=` o `?cp=` (el CP quedaría en la URL y el servidor tendría que resolver la referencia) y devolver un array agrupado de bibliotecas (refactor mayor del contrato).

### 6. Ordenación en cliente y agrupación por códigos

`LibrariesTable` pasa a cliente. La clave de grupo pasa de nombres a `${biblioteca_codigo}|||${sucursal_codigo ?? sucursal_nombre ?? ""}`, usando los nombres del primer ejemplar para mostrar. Así la ubicación se asocia a la sucursal correcta aunque haya nombres repetidos.

El componente:

- Ofrece un selector de CP con etiqueta “28015 — Madrid” y permite limpiar la elección.
- Guarda el CP en `localStorage` (`mediateca:codigo-postal`); lo lee en `useEffect` para no provocar un mismatch de hidratación. Sin CP, el orden es alfabético.
- Resuelve la ubicación del grupo con esta precedencia: coordenadas de `ubicacion`, centroide del `codigo_postal` en el JSON, o sin ubicación.
- Calcula la distancia Haversine (radio 6371 km) y muestra “≈ 3,2 km” o “≈ 800 m”.
- Coloca las sucursales sin ubicación al final, ordenadas alfabéticamente. Si ninguna tiene ubicación, mantiene el alfabético y muestra un aviso.
- Anuncia el estado del orden con `aria-live`.

`apps/web/lib/geo.ts` concentra `haversineKm` y `formatDistance`. No se añade dependencia nueva.

Alternativas descartadas: ordenar en el servidor y reflejar el CP en la URL (más trabajo y estado compartible innecesario en v1) y geolocalización del navegador (bloqueada por HTTP).

### 7. Migración y versión de esquema

`SCHEMA_VERSION` pasa a `5`. Se añade `services/enrich/scripts/migrate_sucursales_geo.sql` idempotente que:

- Crea `sucursales` si no existe, con `codigo` único e índice por `biblioteca_id`.
- Añade `bibliotecas.codigo_postal` si no existe.
- Actualiza `schema_meta.schema_version` a `5`.

En bases nuevas, `Base.metadata.create_all` crea la tabla y la columna. En bases existentes se aplica `make migrate`. No se introduce Alembic.

### 8. Distancias y degradación

La distancia es aproximada y se etiqueta como tal. El CP de referencia se resuelve con el centroide del JSON; la sucursal se resuelve con sus coordenadas o, si faltan, con el centroide de su CP. Si no hay ninguna de las dos, la sucursal va al final. Esto evita inventar coordenadas y mantiene una ordenación útil con los datos disponibles.

## Risks / Trade-offs

- **Scraping frágil del directorio** → parser con fixtures de fichas reales, omisión limpia de fichas no válidas y resumen de cobertura; no se guarda HTML.
- **Cobertura incompleta de `ll=`** → las sucursales sin coordenadas usan el centroide de su CP; la precisión es de CP y se muestra como aproximada.
- **Centroides de CP imprecisos** → se documenta la fuente y la aproximación; la geocodificación de direcciones queda como mejora posterior.
- **Licencias de los datos de CP** → el JSON incluye fuente y licencia; la ficha y el README muestran la atribución (kodens, MIT; INE, CC BY 4.0).
- **Datos de CP congelados** → script reproducible y JSON versionado; solo hay que regenerarlo cuando cambien las fuentes.
- **Reordenación tras el primer render** → el CP se lee en `useEffect`; el primer render es alfabético en servidor y cliente. Se puede pasar a cookie o URL en el futuro.
- **Relación viewonly poco convencional** → se carga explícitamente con `selectinload`; si falla, se sustituye por un mapa de sucursales en el router.
- **Cambio de contrato** → el campo es opcional; se regeneran contrato y tipos y se añaden pruebas de la ficha con y sin ubicación.
- **Despliegue coordinado por `SCHEMA_VERSION`** → `make migrate` antes de arrancar la API; el servicio `init` ya aplica las migraciones.
- **Bibliobuses y bibliotecas móviles** → no se usan coordenadas de paradas; se conserva CP/municipio y se ordenan por CP o al final.
- **Sin tests de portal** → validación con TypeScript/build y QA manual en v1; Vitest queda como mejora posterior.

## Migration Plan

1. Actualizar `packages/shared`: `Sucursal`, `Biblioteca.codigo_postal`, `UbicacionOut`, `EjemplarOut.ubicacion` y `SCHEMA_VERSION = "5"`.
2. Añadir la migración `migrate_sucursales_geo.sql` y verificar que es idempotente.
3. Implementar el parser, repositorio y comando `refresh-branches` en `services/enrich`, con fixtures y pruebas.
4. Actualizar el serializador y el router de records en `services/api`, con pruebas de los casos con y sin ubicación.
5. Generar el JSON de CP y ajustar `LibrariesTable`, `geo.ts` y la ficha.
6. Regenerar `contracts/openapi.json` y `apps/web/lib/api-types.ts` con `make contracts`.
7. Ejecutar `make test` y `make lint`; compilar el portal.
8. Desplegar: `make migrate`, `make branches`, reconstruir las dos imágenes y arrancar `init` antes de API y portal.
9. Verificar una ficha con sucursales en Madrid y Alcalá: ubicación presente, orden por CP y distancias.

Rollback: los cambios de esquema son aditivos (tabla y columna nuevas) y el código anterior las ignora. Para revertir las imágenes, hay que devolver `schema_meta.schema_version` a `4` después de revertir la API, porque la comprobación de arranque exige coincidencia exacta; la tabla y la columna nuevas pueden permanecer sin uso.

## Open Questions

- ¿Se programará la actualización del directorio en el scheduler en un cambio posterior? No afecta al diseño ni a las tareas de esta versión.
- ¿Se promoverá el CP seleccionado a cookie o parámetro de URL para compartir el estado? Es una mejora de UX posterior; v1 usa `localStorage`.
