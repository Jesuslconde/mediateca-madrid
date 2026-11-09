import Link from "next/link";

import { FacetFilters } from "@/components/FacetFilters";
import { RecordCard } from "@/components/RecordCard";
import { SearchBar } from "@/components/SearchBar";
import { getLibraries, searchRecords } from "@/lib/api";
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

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const sp = await searchParams;
  const query = first(sp.q)?.trim() ?? "";
  const supports = toArray(sp.soporte);
  const genero = first(sp.genero);
  const idioma = first(sp.idioma);
  const biblioteca = first(sp.biblioteca);
  const anioDesde = parseYear(first(sp.anio_desde));
  const anioHasta = parseYear(first(sp.anio_hasta));
  const page = Math.max(1, Number(first(sp.page) ?? "1") || 1);
  const sort = first(sp.sort) ?? "relevancia";

  const [result, libraries] = await Promise.all([
    searchRecords({
      q: query || undefined,
      soporte: supports.length ? supports : undefined,
      genero,
      idioma,
      biblioteca,
      anio_desde: anioDesde,
      anio_hasta: anioHasta,
      page,
      limit: 20,
      sort,
    }).catch(() => null),
    getLibraries().catch(() => []),
  ]);

  const activeFilters = [
    ...supports.map((support) => `Soporte: ${support}`),
    genero ? `Género: ${genero}` : null,
    biblioteca ? `Biblioteca: ${biblioteca}` : null,
    idioma ? `Idioma: ${idioma}` : null,
    anioDesde || anioHasta ? `Año: ${anioDesde ?? "..."}–${anioHasta ?? "..."}` : null,
  ].filter(Boolean) as string[];

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card sm:p-5">
        <SearchBar defaultValue={query} compact />
      </section>

      <div className="grid gap-8 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <h2 className="mb-4 text-sm font-bold uppercase tracking-wider text-slate-500">
              Filtros
            </h2>
            <FacetFilters
              params={sp}
              facets={result?.facets ?? {}}
              libraries={libraries}
            />
          </div>
        </aside>

        <section className="min-w-0 space-y-4">
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-2xl font-black text-ink">
                {query ? `Resultados para “${query}”` : "Todo el catálogo"}
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                {result
                  ? `${result.total.toLocaleString("es-ES")} ediciones · ${result.took_ms} ms`
                  : "No se pudo consultar el índice"}
              </p>
            </div>
            {result && result.total_pages > 1 ? (
              <p className="text-sm text-slate-500">
                Página {result.page} de {result.total_pages}
              </p>
            ) : null}
          </header>

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
                <RecordCard key={hit.id} hit={hit} />
              ))}
            </div>
          )}

          {result && result.total_pages > 1 ? (
            <nav className="flex items-center justify-between gap-3 pt-2" aria-label="Paginación">
              {result.page > 1 ? (
                <Link
                  href={`/buscar?${buildSearchQuery(sp, { page: String(result.page - 1) })}`}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Anterior
                </Link>
              ) : (
                <span className="rounded-xl border border-slate-100 px-4 py-2 text-sm text-slate-300">
                  Anterior
                </span>
              )}
              <span className="text-sm text-slate-500">
                {result.page} / {result.total_pages}
              </span>
              {result.page < result.total_pages ? (
                <Link
                  href={`/buscar?${buildSearchQuery(sp, { page: String(result.page + 1) })}`}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Siguiente
                </Link>
              ) : (
                <span className="rounded-xl border border-slate-100 px-4 py-2 text-sm text-slate-300">
                  Siguiente
                </span>
              )}
            </nav>
          ) : null}
        </section>
      </div>
    </div>
  );
}
