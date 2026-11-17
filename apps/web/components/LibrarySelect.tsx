"use client";

import { useMemo, useState } from "react";

import type { Location } from "@/lib/api";

type Group = {
  key: string;
  label: string;
  items: Location[];
};

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function sortGroups(groups: Group[]): Group[] {
  return groups.sort((a, b) => a.label.localeCompare(b.label, "es"));
}

function sortItems(items: Location[]): Location[] {
  return items.sort((a, b) => {
    if (a.tipo !== b.tipo) return a.tipo === "biblioteca" ? -1 : 1;
    return a.nombre.localeCompare(b.nombre, "es");
  });
}

function legacyLocation(codigo: string): Location {
  return {
    codigo,
    nombre: codigo,
    tipo: "biblioteca",
    biblioteca_codigo: codigo,
    biblioteca_nombre: codigo,
    municipio: null,
    ejemplares: 0,
  };
}

export function LibrarySelect({
  locations,
  defaultValue,
}: {
  locations: Location[];
  defaultValue?: string;
}) {
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(defaultValue ?? "");

  const groups = useMemo(() => {
    const term = normalize(filter);
    const matches = term
      ? locations.filter(
          (location) =>
            normalize(location.nombre).includes(term) ||
            normalize(location.biblioteca_nombre).includes(term),
        )
      : locations;
    const grouped = new Map<string, Group>();
    for (const location of matches) {
      const key = location.biblioteca_codigo || location.codigo;
      const current = grouped.get(key) ?? {
        key,
        label: location.biblioteca_nombre || location.nombre,
        items: [],
      };
      current.items.push(location);
      grouped.set(key, current);
    }
    const result = sortGroups([...grouped.values()]);
    for (const group of result) {
      sortItems(group.items);
    }

    if (selected && !matches.some((location) => location.codigo === selected)) {
      const selectedLocation =
        locations.find((location) => location.codigo === selected) ??
        legacyLocation(selected);
      const key = selectedLocation.biblioteca_codigo || selectedLocation.codigo;
      let group = result.find((candidate) => candidate.key === key);
      if (group === undefined) {
        group = {
          key,
          label: selectedLocation.biblioteca_nombre || selectedLocation.nombre,
          items: [],
        };
        result.push(group);
        sortGroups(result);
      }
      group.items.unshift(selectedLocation);
    }

    return result;
  }, [filter, locations, selected]);

  const hasOptions = groups.some((group) => group.items.length > 0);

  return (
    <div className="space-y-2">
      <input
        type="search"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        placeholder="Escribe biblioteca o sucursal"
        aria-label="Filtrar bibliotecas y sucursales por texto"
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
        {groups.map((group) => (
          <optgroup key={group.key} label={group.label}>
            {group.items.map((location) => (
              <option key={location.codigo} value={location.codigo}>
                {location.tipo === "biblioteca"
                  ? "Toda la biblioteca"
                  : location.nombre}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      {filter && !hasOptions ? (
        <p className="text-xs text-slate-400">No hay bibliotecas que coincidan.</p>
      ) : null}
    </div>
  );
}
