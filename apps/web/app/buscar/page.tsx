import Link from "next/link";
import { Suspense } from "react";

import { FacetFilters } from "@/components/FacetFilters";
import { PaginationLink } from "@/components/PaginationLink";
import { RecordCard } from "@/components/RecordCard";
import { SearchBar, type SearchField } from "@/components/SearchBar";
import { SearchSkeleton } from "@/components/SearchSkeleton";
import { SortSelect } from "@/components/SortSelect";
import { getLocations, searchRecords } from "@/lib/api";
import { getActiveList, savedRecordIds } from "@/lib/active-list";
import { countryLabel } from "@/lib/labels";
import { parseSort, type SortValue } from "@/lib/sort";
import {
  buildSearchQuery,
  first,
  toArray,
  type RawSearchParams,
} from "@/lib/url";

export const dynamic = "force-dynamic";

function parseYear(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

type SearchBodyProps = {
  sp: RawSearchParams;
  query: string;
  campo: SearchField;
  supports: string[];
  genero?: string;
  idioma?: string;
  countries: string[];
  biblioteca?: string;
  fuente?: string;
  anioDesde?: number;
  anioHasta?: number;
  page: number;
  sort: SortValue;
  volver: string;
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const sp = await searchParams;
  const query = first(sp.q)?.trim() ?? "";
  const campo: SearchField = first(sp.campo) === "titn" ? "titn" : "todo";
  const supports = toArray(sp.soporte);
  const genero = first(sp.genero);
  const idioma = first(sp.idioma);
  const countries = toArray(sp.paises_origen);
  const biblioteca = first(sp.biblioteca);
  const fuente = first(sp.fuente);
  const anioDesde = parseYear(first(sp.anio_desde));
  const anioHasta = parseYear(first(sp.anio_hasta));
  const page = Math.max(1, Number(first(sp.page) ?? "1") || 1);
  const sort = parseSort(first(sp.sort));

  const searchQuery = buildSearchQuery(sp, { volver: undefined });
  const volver = `/buscar${searchQuery ? `?${searchQuery}` : ""}`;
  const suspenseKey = [
    query,
    campo,
    supports.join(","),
    genero ?? "",
    idioma ?? "",
    countries.join(","),
    biblioteca ?? "",
    fuente ?? "",
    anioDesde ?? "",
    anioHasta ?? "",
    page,
    sort,
  ].join("|");

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card sm:p-5">
        <SearchBar defaultValue={query} campo={campo} compact />
      </section>

      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-ink">
            {query
              ? campo === "titn"
                ? `Resultados para TITN “${query}”`
                : `Resultados para “${query}”`
              : "Todo el catálogo"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Filtra el catálogo y elige cómo ordenar los resultados.
          </p>
        </div>
        <Suspense fallback={<div className="h-10 w-52 animate-pulse rounded-xl bg-slate-100" />}>
          <SortSelect value={sort} />
        </Suspense>
      </header>

      <Suspense key={suspenseKey} fallback={<SearchSkeleton />}>
        <SearchBody
          sp={sp}
          query={query}
          campo={campo}
          supports={supports}
          genero={genero}
          idioma={idioma}
          countries={countries}
          biblioteca={biblioteca}
          fuente={fuente}
          anioDesde={anioDesde}
          anioHasta={anioHasta}
          page={page}
          sort={sort}
          volver={volver}
        />
      </Suspense>
    </div>
  );
}

async function SearchBody({
  sp,
  query,
  campo,
  supports,
  genero,
  idioma,
  countries,
  biblioteca,
  fuente,
  anioDesde,
  anioHasta,
  page,
  sort,
  volver,
}: SearchBodyProps) {
  const [result, locations, activeList] = await Promise.all([
    searchRecords({
      q: campo === "titn" ? undefined : query || undefined,
      titn: campo === "titn" ? query || undefined : undefined,
      soporte: supports.length ? supports : undefined,
      genero,
      idioma,
      paises_origen: countries.length ? countries : undefined,
      biblioteca,
      fuente,
      anio_desde: anioDesde,
      anio_hasta: anioHasta,
      page,
      limit: 20,
      sort,
    }).catch(() => null),
    getLocations().catch(() => []),
    getActiveList().catch(() => null),
  ]);
  const saved = savedRecordIds(activeList);

  const selectedLocation = locations.find(
    (location) => location.codigo === biblioteca,
  );
  const bibliotecaLabel = selectedLocation
    ? selectedLocation.tipo === "biblioteca"
      ? selectedLocation.nombre
      : `${selectedLocation.biblioteca_nombre} — ${selectedLocation.nombre}`
    : biblioteca;
  const activeFilters = [
    ...supports.map((support) => `Soporte: ${support}`),
    genero ? `Género: ${genero}` : null,
    ...countries.map((country) => `País: ${countryLabel(country) ?? country}`),
    bibliotecaLabel ? `Biblioteca: ${bibliotecaLabel}` : null,
    fuente ? `Fuente: ${fuente}` : null,
    idioma ? `Idioma: ${idioma}` : null,
    anioDesde || anioHasta
      ? `Año: ${anioDesde ?? "..."}–${anioHasta ?? "..."}`
      : null,
  ].filter(Boolean) as string[];

  return (
    <div className="space-y-4">
      {activeFilters.length ? (
        <div className="flex flex-wrap gap-2">
          {activeFilters.map((filter) => (
            <span
              key={filter}
              className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600"
            >
              {filter}
            </span>
          ))}
        </div>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-slate-500">
              Filtros
            </h2>
            <FacetFilters
              params={sp}
              facets={result?.facets ?? {}}
              locations={locations}
            />
          </div>
        </aside>

        <section className="min-w-0 space-y-4">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="text-sm text-slate-500">
            {result
              ? `${result.total.toLocaleString("es-ES")} obras · ${result.total_ediciones.toLocaleString("es-ES")} ediciones · ${result.took_ms} ms`
              : "No se pudo consultar el índice"}
          </p>
          {result && result.total_pages > 1 ? (
            <p className="text-sm text-slate-500">
              Página {result.page} de {result.total_pages}
            </p>
          ) : null}
        </header>

        {!result ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">
            <p className="font-semibold">No se pudo conectar con la API.</p>
            <p className="mt-1">
              Comprueba que el servicio <code>api</code> está levantado y que el índice tiene
              datos. Puedes ejecutar <code>make harvest</code> para recolectar del OPAC.
            </p>
          </div>
        ) : result.hits.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-lg font-bold text-ink">No hay resultados</p>
            <p className="mt-2 text-sm text-slate-500">
              Prueba con otro término o elimina algún filtro.
            </p>
            <Link
              href="/buscar"
              className="mt-4 inline-block rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
            >
              Limpiar búsqueda
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {result.hits.map((hit) => (
              <RecordCard
                key={hit.id}
                hit={hit}
                volver={volver}
                saved={saved.has(hit.record_id ?? hit.titn)}
              />
            ))}
          </div>
        )}

        {result && result.total_pages > 1 ? (
          <nav className="flex items-center justify-between gap-3 pt-2" aria-label="Paginación">
            <PaginationLink
              href={
                result.page > 1
                  ? `/buscar?${buildSearchQuery(sp, { page: String(result.page - 1) })}`
                  : undefined
              }
            >
              Anterior
            </PaginationLink>
            <span className="text-sm text-slate-500">
              {result.page} / {result.total_pages}
            </span>
            <PaginationLink
              href={
                result.page < result.total_pages
                  ? `/buscar?${buildSearchQuery(sp, { page: String(result.page + 1) })}`
                  : undefined
              }
            >
              Siguiente
            </PaginationLink>
          </nav>
        ) : null}
        </section>
      </div>
    </div>
  );
}
