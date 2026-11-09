import Link from "next/link";

import type { Library } from "@/lib/api";
import { languageLabel } from "@/lib/labels";
import { buildSearchQuery, first, toArray, type RawSearchParams } from "@/lib/url";

const DEFAULT_SUPPORTS = ["DVD", "Blu-ray", "4K UHD"];

function sortedEntries(
  values: Record<string, number> | undefined,
  selected?: string,
): [string, number][] {
  const entries = Object.entries(values ?? {}).sort((a, b) => b[1] - a[1]);
  if (selected && !entries.some(([key]) => key === selected)) {
    entries.unshift([selected, 0]);
  }
  return entries;
}

export function FacetFilters({
  params,
  facets,
  libraries,
}: {
  params: RawSearchParams;
  facets: Record<string, Record<string, number>>;
  libraries: Library[];
}) {
  const selectedSupports = toArray(params.soporte);
  const selectedGenero = first(params.genero);
  const selectedIdioma = first(params.idioma);
  const selectedBiblioteca = first(params.biblioteca);
  const selectedSort = first(params.sort) ?? "relevancia";
  const query = first(params.q) ?? "";

  const supportEntries = DEFAULT_SUPPORTS.map((support) => [
    support,
    facets.soportes?.[support] ?? 0,
  ]) as [string, number][];
  for (const [support, count] of Object.entries(facets.soportes ?? {})) {
    if (!supportEntries.some(([value]) => value === support)) {
      supportEntries.push([support, count]);
    }
  }

  const genreEntries = sortedEntries(facets.generos, selectedGenero).slice(0, 40);
  const languageEntries = sortedEntries(facets.idioma, selectedIdioma).slice(0, 40);
  const libraryOptions = selectedBiblioteca
    ? libraries.some((library) => library.nombre === selectedBiblioteca)
      ? libraries
      : [
          ...libraries,
          {
            codigo: "",
            nombre: selectedBiblioteca,
            municipio: null,
            ejemplares: 0,
          },
        ]
    : libraries;

  return (
    <form action="/buscar" method="get" className="space-y-6">
      {query ? <input type="hidden" name="q" value={query} /> : null}

      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
          Soporte
        </h3>
        <div className="space-y-2">
          {supportEntries.map(([support, count]) => (
            <label key={support} className="flex items-center justify-between gap-2 text-sm">
              <span className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="soporte"
                  value={support}
                  defaultChecked={selectedSupports.includes(support)}
                  className="h-4 w-4 rounded border-slate-300 text-ink focus:ring-ink"
                />
                {support}
              </span>
              {count > 0 ? <span className="text-xs text-slate-400">{count}</span> : null}
            </label>
          ))}
        </div>
      </section>

      <section>
        <label htmlFor="genero" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
          Género
        </label>
        <select
          id="genero"
          name="genero"
          defaultValue={selectedGenero ?? ""}
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {genreEntries.map(([genre, count]) => (
            <option key={genre} value={genre}>
              {genre} ({count})
            </option>
          ))}
        </select>
      </section>

      <section>
        <label htmlFor="biblioteca" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
          Biblioteca
        </label>
        <select
          id="biblioteca"
          name="biblioteca"
          defaultValue={selectedBiblioteca ?? ""}
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
        >
          <option value="">Todas</option>
          {libraryOptions.map((library) => (
            <option key={`${library.codigo}-${library.nombre}`} value={library.nombre}>
              {library.nombre}
            </option>
          ))}
        </select>
      </section>

      <section>
        <label htmlFor="idioma" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
          Idioma
        </label>
        <select
          id="idioma"
          name="idioma"
          defaultValue={selectedIdioma ?? ""}
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
        >
          <option value="">Todos</option>
          {languageEntries.map(([language, count]) => (
            <option key={language} value={language}>
              {languageLabel(language) ?? language} ({count})
            </option>
          ))}
        </select>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">Año</h3>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            name="anio_desde"
            min="1900"
            max="2100"
            placeholder="Desde"
            defaultValue={first(params.anio_desde) ?? ""}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
          />
          <input
            type="number"
            name="anio_hasta"
            min="1900"
            max="2100"
            placeholder="Hasta"
            defaultValue={first(params.anio_hasta) ?? ""}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
          />
        </div>
      </section>

      <section>
        <label htmlFor="sort" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
          Ordenar por
        </label>
        <select
          id="sort"
          name="sort"
          defaultValue={selectedSort}
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
        >
          <option value="relevancia">Relevancia</option>
          <option value="anio_desc">Año (más reciente)</option>
          <option value="anio_asc">Año (más antiguo)</option>
          <option value="titulo_asc">Título (A-Z)</option>
          <option value="duracion_asc">Duración (menor)</option>
        </select>
      </section>

      <div className="flex flex-col gap-2">
        <button
          type="submit"
          className="rounded-xl bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          Aplicar filtros
        </button>
        <Link
          href={`/buscar${query ? `?${buildSearchQuery({ q: query })}` : ""}`}
          className="rounded-xl border border-slate-200 px-4 py-2.5 text-center text-sm font-medium text-slate-600 transition hover:bg-slate-100"
        >
          Limpiar filtros
        </Link>
      </div>
    </form>
  );
}
