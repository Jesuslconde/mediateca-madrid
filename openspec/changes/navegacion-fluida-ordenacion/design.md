# Design

## Context

Ver `proposal.md` para la motivación. El estado actual que condiciona el diseño:

- Next.js 15.5 con App Router, React 19 y Tailwind 3.4. Todas las páginas son `force-dynamic` y piden datos server-side con `cache: "no-store"` (`apps/web/app/buscar/page.tsx`, `apps/web/lib/api.ts`).
- La búsqueda y los filtros son formularios GET nativos (`apps/web/components/SearchBar.tsx`, `apps/web/components/FacetFilters.tsx`), por lo que provocan navegación de documento completa.
- La paginación ya usa `<Link>`, pero no hay ningún estado de carga ni esqueleto.
- La API ya acepta `sort` con los valores `relevancia`, `anio_desc`, `anio_asc`, `titulo_asc` y `duracion_asc` (`services/api/src/mediateca/api/routers/search.py`).
- Meilisearch ya declara `anio`, `titulo` y `duracion_min` como campos ordenables (`services/enrich/src/mediateca/catalog/indexer.py`).
- El portal no tiene librería de datos ni harness de tests de frontend.

## Goals / Non-Goals

**Goals:**

- Navegación cliente con la URL como fuente de verdad, sin recarga de documento.
- Ordenación visible e inmediata, estable y compatible con filtros y paginación.
- Carga percibida moderna: esqueletos al entrar o cambiar parámetros y estado pendiente en paginación.
- Vuelta de la ficha a la búsqueda con el estado previo, incluso en pestaña nueva.

**Non-Goals:**

- Cache cliente, prefetch de datos o proxy BFF (opción descartada en la exploración).
- Normalización de artículos iniciales, acentos o puntuación del título.
- Cambiar los valores públicos de `sort` o el contrato OpenAPI.
- Añadir un framework de tests de frontend.
- Reindexar el catálogo.

## Decisions

### Navegación cliente con `next/form`

Se sustituyen los `<form>` nativos por `next/form` de Next.js 15 en el buscador y en los filtros. `next/form` mantiene la semántica GET, la URL compartible y el funcionamiento sin JavaScript, pero realiza navegación cliente cuando JavaScript está disponible.

Alternativas consideradas:

- **Formulario cliente con `onSubmit` y `router.push`**: más código y hay que reimplementar la serialización de campos.
- **Convertir toda la página a cliente**: pierde el render en servidor y complica la carga inicial.

### Selector de orden en la cabecera

Nuevo componente cliente `SortSelect` en la cabecera de resultados. Usa `usePathname`, `useSearchParams`, `useRouter` y `useTransition`. Al cambiar:

1. Copia los parámetros actuales.
2. Fija `sort`.
3. Elimina `page` para volver a la primera página.
4. Ejecuta `router.replace(url, { scroll: false })`.

Se usa `replace` para no llenar el historial con cada cambio de orden. El selector del panel lateral se elimina y `FacetFilters` incluye un `input` oculto con el `sort` activo para que aplicar un filtro no pierda el orden.

Alternativa considerada: mantener el selector en el panel de filtros. Se descarta porque obliga a pulsar «Aplicar filtros» y no cumple la inmediatez pedida.

### Orden estable en el backend

`SORT_MAP` pasa de `dict[str, str | None]` a `dict[str, list[str] | None]`:

```text
relevancia   -> None
anio_desc    -> ["anio:desc", "titulo:asc"]
anio_asc     -> ["anio:asc", "titulo:asc"]
titulo_asc   -> ["titulo:asc"]
duracion_asc -> ["duracion_min:asc", "titulo:asc"]
```

`CatalogSearch.search` acepta `list[str] | None` y lo pasa a Meilisearch en `options["sort"]`. Meilisearch aplica los criterios en orden, de modo que el título desempata año y duración. Los documentos sin valor en el campo ordenado quedan al final según el comportamiento de Meilisearch; se acepta porque el índice de búsqueda solo devuelve fichas enriquecidas.

Alternativas consideradas:

- **Ordenar en el frontend**: incorrecto con resultados paginados.
- **Añadir un campo compuesto al índice**: exigiría reindexar y no aporta frente a los criterios múltiples de Meilisearch.

### Esqueletos y `Suspense`

La página de resultados se divide en:

- Un armazón que resuelve `searchParams` y renderiza el buscador y la cabecera.
- Un componente asíncrono `SearchBody` que hace la única llamada a la API y a bibliotecas, envuelto en `<Suspense key={paramsSerializados} fallback={<SearchSkeleton />}>`.

La `key` basada en los parámetros garantiza que cada nueva búsqueda muestre el esqueleto en lugar de mantener resultados antiguos. Se añade `app/buscar/loading.tsx` para la entrada inicial desde otra ruta y `app/registro/[titn]/loading.tsx` para la ficha. La paginación usa `useLinkStatus` dentro de un componente hijo de `<Link>` para mostrar el estado pendiente.

Alternativa considerada: confiar solo en `loading.tsx`. No cubre de forma fiable los cambios de `searchParams` dentro de la misma ruta.

### Vuelta con el estado previo mediante `volver`

`RecordCard` recibe la URL de búsqueda actual serializada y enlaza a:

```text
/registro/<titn>?volver=<url-encoded-/buscar?...>
```

La ficha lee `volver` de `searchParams` y lo valida antes de usarlo: debe empezar por `/buscar` y no por `//`, para evitar redirecciones externas. Si no es válido, el enlace apunta a `/buscar`.

Alternativas consideradas:

- **`router.back()`**: falla al abrir la ficha en una pestaña nueva o al recargar.
- **`sessionStorage`**: no funciona en pestaña nueva y añade estado oculto.

### Sin reindexado

Los campos ordenables ya están declarados en `SORTABLE_ATTRIBUTES` y `ensure_index` aplica la configuración. No hay cambio de esquema de índice ni migración. Como verificación operativa, se comprobará que el índice existente tiene `anio`, `titulo` y `duracion_min` en `sortableAttributes`.

## Risks / Trade-offs

- **`next/form` descarta parámetros que no estén en el formulario** → el buscador mantiene el comportamiento actual de iniciar una búsqueda nueva; los filtros incluyen todos sus campos y un `sort` oculto.
- **`useSearchParams` exige una frontera de `Suspense`** → todos los componentes que lo usan se envuelven en `Suspense` aunque las páginas sean dinámicas.
- **Doble petición si el armazón también pide datos** → solo `SearchBody` llama a la API; el armazón se limita a resolver parámetros.
- **Salto de layout al mostrar el esqueleto** → el esqueleto replica la altura y el espaciado de las tarjetas y del panel lateral.
- **`volver` malicioso o externo** → validación estricta de ruta interna que empiece por `/buscar`.
- **Orden alfabético poco natural con artículos y acentos** → se documenta como limitación y se deja para un cambio específico con campo normalizado.
- **Sin tests de frontend** → la verificación combina un test de API para la ordenación estable y una checklist manual de navegación, orden, atrás/adelante y teclado.
- **Cambios rápidos de orden** → `useTransition` mantiene la interfaz responsiva y Next.js descarta la navegación obsoleta; el selector refleja siempre el valor de la URL.

## Migration Plan

- Sin migraciones de base de datos ni reindexado.
- Desplegar API y web juntas; el orden de despliegue no rompe compatibilidad porque los valores de `sort` no cambian.
- Rollback: volver a las imágenes anteriores; no hay cambios de datos que revertir.
- Verificación posterior: abrir una búsqueda, ordenar por año y comprobar empates por título; aplicar un filtro y confirmar que el orden se conserva; abrir una ficha y volver.

## Open Questions

Ninguna que bloquee el diseño. La ordenación natural de títulos (artículos y acentos) queda como cambio futuro independiente.
