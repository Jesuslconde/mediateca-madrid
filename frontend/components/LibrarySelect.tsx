"use client";

import { useMemo, useState } from "react";

import type { Library } from "@/lib/api";

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export function LibrarySelect({
  libraries,
  defaultValue,
}: {
  libraries: Library[];
  defaultValue?: string;
}) {
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(defaultValue ?? "");

  const options = useMemo(() => {
    const term = normalize(filter);
    const matches = term
      ? libraries.filter((library) => normalize(library.nombre).includes(term))
      : libraries;

    if (
      selected &&
      !matches.some((library) => library.nombre === selected)
    ) {
      const selectedLibrary = libraries.find((library) => library.nombre === selected);
      if (selectedLibrary) {
        return [selectedLibrary, ...matches];
      }
    }

    return matches;
  }, [filter, libraries, selected]);

  return (
    <div className="space-y-2">
      <input
        type="search"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        placeholder="Escribe para filtrar bibliotecas"
        aria-label="Filtrar bibliotecas por texto"
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
      />
      <select
        id="biblioteca"
        name="biblioteca"
        value={selected}
        onChange={(event) => setSelected(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
      >
        <option value="">Todas</option>
        {options.map((library) => (
          <option key={`${library.codigo}-${library.nombre}`} value={library.nombre}>
            {library.nombre}
          </option>
        ))}
      </select>
      {filter && options.length === 0 ? (
        <p className="text-xs text-slate-400">No hay bibliotecas que coincidan.</p>
      ) : null}
    </div>
  );
}
