"use client";

import { useState } from "react";

import type { Location } from "@/lib/api";
import { formatDistance } from "@/lib/geo";

export function NearbyLibraryPicker({
  locations,
  excluded,
  enabled,
}: {
  locations: Location[];
  excluded: string[];
  enabled: boolean;
}) {
  const [excludedCodes, setExcludedCodes] = useState<Set<string>>(
    () => new Set(excluded),
  );

  if (!enabled || locations.length === 0) return null;

  function toggle(codigo: string) {
    setExcludedCodes((previous) => {
      const next = new Set(previous);
      if (next.has(codigo)) {
        next.delete(codigo);
      } else {
        next.add(codigo);
      }
      return next;
    });
  }

  function label(location: Location): string {
    return location.tipo === "biblioteca"
      ? `Toda la biblioteca: ${location.nombre}`
      : `${location.biblioteca_nombre} — ${location.nombre}`;
  }

  return (
    <section>
      <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
        Bibliotecas cercanas
      </h3>
      {[...excludedCodes].map((codigo) => (
        <input key={codigo} type="hidden" name="excluir" value={codigo} />
      ))}
      <div className="space-y-2">
        {locations.map((location) => (
          <label
            key={location.codigo}
            className="flex items-center justify-between gap-2 text-sm"
          >
            <span className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!excludedCodes.has(location.codigo)}
                onChange={() => toggle(location.codigo)}
                className="h-4 w-4 rounded border-slate-300 text-ink focus:ring-ink"
              />
              {label(location)}
            </span>
            {location.distancia_km !== null &&
            location.distancia_km !== undefined ? (
              <span className="text-xs text-slate-400">
                {formatDistance(location.distancia_km)}
              </span>
            ) : null}
          </label>
        ))}
      </div>
      <p className="mt-1 text-xs text-slate-400">
        Desmarca las bibliotecas que quieras excluir de la búsqueda.
      </p>
    </section>
  );
}
