# Tasks

## 1. Orden estable en la API

- [ ] 1.1 Cambiar `SORT_MAP` en `services/api/src/mediateca/api/routers/search.py` a listas de criterios y adaptar `CatalogSearch.search` en `services/api/src/mediateca/catalog/search.py` para aceptar `list[str] | None`; verificar que `make test-api` sigue pasando.
- [ ] 1.2 Añadir a `services/api/tests/test_api.py` un test que compruebe que `anio_desc` envía `["anio:desc", "titulo:asc"]`, `anio_asc` envía `["anio:asc", "titulo:asc"]` y `duracion_asc` envía `["duracion_min:asc", "titulo:asc"]`; verificar con `make test-api`.

## 2. Búsqueda y filtros con navegación cliente

- [ ] 2.1 Sustituir el `<form>` de `apps/web/components/SearchBar.tsx` por `next/form`; verificar en el navegador que buscar desde la portada no genera una petición de documento nueva y que la URL contiene `q`.
- [ ] 2.2 Sustituir el `<form>` de `apps/web/components/FacetFilters.tsx` por `next/form` y añadir un `input` oculto con el `sort` activo; verificar que aplicar un filtro no recarga el documento y que el orden se conserva.

## 3. Ordenación en la cabecera de resultados

- [ ] 3.1 Crear `apps/web/components/SortSelect.tsx` como componente cliente con `usePathname`, `useSearchParams`, `useRouter` y `useTransition`; verificar que al cambiar el orden se actualizan los resultados sin pulsar «Aplicar filtros» y que desaparece `page` de la URL.
- [ ] 3.2 Quitar el selector de orden de `FacetFilters` y colocarlo en la cabecera de `apps/web/app/buscar/page.tsx`; verificar que no hay controles duplicados y que aplicar un filtro conserva el orden activo.
- [ ] 3.3 Validar el parámetro `sort` en la página de resultados y caer a `relevancia` cuando no sea uno de los valores admitidos; verificar que `/buscar?sort=foo` muestra resultados en vez de un error de la API.

## 4. Estado de carga visible

- [ ] 4.1 Extraer el fetch de resultados a un componente asíncrono `SearchBody` envuelto en `<Suspense key={parámetros} fallback={<SearchSkeleton />}>` en `apps/web/app/buscar/page.tsx`; verificar que cada cambio de búsqueda muestra el esqueleto y que solo se hace una petición a `/api/search` por cambio.
- [ ] 4.2 Añadir `apps/web/app/buscar/loading.tsx` y `apps/web/app/registro/[titn]/loading.tsx` con esqueletos coherentes con las tarjetas y la ficha; verificar que al navegar desde la portada o desde los resultados se ve el estado de carga.
- [ ] 4.3 Crear un componente de paginación cliente que use `useLinkStatus` dentro de `<Link>` para mostrar el estado pendiente; verificar que al cambiar de página el enlace indica que está cargando y no hay recarga completa.

## 5. Vuelta a la búsqueda con el estado previo

- [ ] 5.1 Hacer que `RecordCard` reciba la búsqueda actual serializada y enlace a `/registro/<titn>?volver=<ruta-codificada>`; verificar que el enlace generado incluye `q`, filtros, `sort` y `page` cuando están activos.
- [ ] 5.2 Leer `searchParams.volver` en `apps/web/app/registro/[titn]/page.tsx` y usarlo en el enlace de vuelta solo si empieza por `/buscar`; verificar que volver conserva el estado y que una ficha abierta directamente vuelve a `/buscar`.
- [ ] 5.3 Rechazar valores de `volver` externos o protocol-relative como `//dominio`; verificar que `/registro/<titn>?volver=//example.com` usa `/buscar` como destino.

## 6. Integración y verificación

- [ ] 6.1 Ejecutar `cd apps/web && npm run build` y verificar que la compilación de Next.js termina sin errores de tipos ni de rutas.
- [ ] 6.2 Ejecutar `make test-api` y verificar que pasan las pruebas de la API, incluida la nueva de orden estable.
- [ ] 6.3 Verificar manualmente en el navegador: buscar desde la portada, aplicar filtros, cambiar el orden, paginar, abrir una ficha y volver; comprobar que no hay recargas de documento, que la URL es compartible y que todo es navegable por teclado.
- [ ] 6.4 Verificar en la configuración del índice de Meilisearch que `sortableAttributes` incluye `anio`, `titulo` y `duracion_min`.

## Workflow follow-up

- Revisar los artefactos y ejecutar `/opsx-apply` cuando se apruebe el plan.
- Archivar el cambio después de completar y revisar la implementación.
