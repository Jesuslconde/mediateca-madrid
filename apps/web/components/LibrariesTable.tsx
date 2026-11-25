"use client";

import { useEffect, useMemo, useSyncExternalStore, type ChangeEvent } from "react";

import type { Ejemplar } from "@/lib/api";
import postalCodesData from "@/lib/codigos-postales-madrid.json";
import { formatDistance, haversineKm, type Point } from "@/lib/geo";

import { SupportBadge } from "./SupportBadge";

const STORAGE_KEY = "mediateca:codigo-postal";

type PostalCode = {
  codigo: string;
  municipio: string | null;
  latitud: number;
  longitud: number;
};

const POSTAL_CODES = (postalCodesData.codigos as PostalCode[])
  .slice()
  .sort((a, b) => a.codigo.localeCompare(b.codigo, "es"));
const POSTAL_CODE_BY_CODE = new Map(
  POSTAL_CODES.map((postalCode) => [postalCode.codigo, postalCode]),
);

const postalCodeListeners = new Set<() => void>();

function subscribePostalCode(listener: () => void) {
  postalCodeListeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    postalCodeListeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

function getPostalCodeSnapshot() {
  return window.localStorage.getItem(STORAGE_KEY) ?? "";
}

function notifyPostalCodeChange() {
  for (const listener of postalCodeListeners) {
    listener();
  }
}

type LibraryGroup = {
  key: string;
  biblioteca: string;
  sucursal: string | null;
  items: Ejemplar[];
  codigoPostal: string | null;
  point: Point | null;
};

function locationFor(ejemplar: Ejemplar): {
  codigoPostal: string | null;
  point: Point | null;
} {
  const ubicacion = ejemplar.ubicacion;
  const codigoPostal = ubicacion?.codigo_postal ?? null;
  if (
    ubicacion?.latitud !== null &&
    ubicacion?.latitud !== undefined &&
    ubicacion?.longitud !== null &&
    ubicacion?.longitud !== undefined
  ) {
    return {
      codigoPostal,
      point: { latitud: ubicacion.latitud, longitud: ubicacion.longitud },
    };
  }
  if (codigoPostal) {
    const postalCode = POSTAL_CODE_BY_CODE.get(codigoPostal);
    if (postalCode) {
      return {
        codigoPostal,
        point: { latitud: postalCode.latitud, longitud: postalCode.longitud },
      };
    }
  }
  return { codigoPostal, point: null };
}

function groupByLibrary(ejemplares: Ejemplar[]): LibraryGroup[] {
  const groups = new Map<string, LibraryGroup>();
  for (const ejemplar of ejemplares) {
    const key = `${ejemplar.biblioteca_codigo}|||${
      ejemplar.sucursal_codigo ?? ejemplar.sucursal ?? ""
    }`;
    const location = locationFor(ejemplar);
    const existing = groups.get(key);
    if (existing) {
      existing.items.push(ejemplar);
      if (!existing.point && location.point) {
        existing.point = location.point;
        existing.codigoPostal = location.codigoPostal;
      }
      continue;
    }
    groups.set(key, {
      key,
      biblioteca: ejemplar.biblioteca,
      sucursal: ejemplar.sucursal ?? null,
      items: [ejemplar],
      codigoPostal: location.codigoPostal,
      point: location.point,
    });
  }

  return [...groups.values()].sort((a, b) => {
    const byLibrary = a.biblioteca.localeCompare(b.biblioteca, "es");
    if (byLibrary !== 0) return byLibrary;
    return (a.sucursal ?? "").localeCompare(b.sucursal ?? "", "es");
  });
}

function postalCodeLabel(postalCode: PostalCode): string {
  return postalCode.municipio
    ? `${postalCode.codigo} — ${postalCode.municipio}`
    : postalCode.codigo;
}

export function LibrariesTable({
  ejemplares,
  opacUrl,
}: {
  ejemplares: Ejemplar[];
  opacUrl?: string | null;
}) {
  const storedCp = useSyncExternalStore(
    subscribePostalCode,
    getPostalCodeSnapshot,
    () => "",
  );
  const selectedCp = POSTAL_CODE_BY_CODE.has(storedCp) ? storedCp : "";
  const groups = useMemo(() => groupByLibrary(ejemplares), [ejemplares]);

  useEffect(() => {
    if (storedCp && !POSTAL_CODE_BY_CODE.has(storedCp)) {
      window.localStorage.removeItem(STORAGE_KEY);
      notifyPostalCodeChange();
    }
  }, [storedCp]);

  const reference = selectedCp
    ? POSTAL_CODE_BY_CODE.get(selectedCp) ?? null
    : null;

  const sortedGroups = useMemo(() => {
    if (!reference) return groups;
    return [...groups].sort((a, b) => {
      const distanceA = a.point ? haversineKm(a.point, reference) : null;
      const distanceB = b.point ? haversineKm(b.point, reference) : null;
      if (distanceA === null && distanceB === null) {
        return a.biblioteca.localeCompare(b.biblioteca, "es");
      }
      if (distanceA === null) return 1;
      if (distanceB === null) return -1;
      if (distanceA !== distanceB) return distanceA - distanceB;
      const byLibrary = a.biblioteca.localeCompare(b.biblioteca, "es");
      if (byLibrary !== 0) return byLibrary;
      return (a.sucursal ?? "").localeCompare(b.sucursal ?? "", "es");
    });
  }, [groups, reference]);

  const hasLocations = sortedGroups.some((group) => group.point !== null);
  const noLocations = Boolean(reference) && !hasLocations;
  const unknownPostalCode = Boolean(selectedCp) && !reference;

  function handlePostalCodeChange(event: ChangeEvent<HTMLSelectElement>) {
    const value = event.target.value;
    if (value) {
      window.localStorage.setItem(STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    notifyPostalCodeChange();
  }

  function clearPostalCode() {
    window.localStorage.removeItem(STORAGE_KEY);
    notifyPostalCodeChange();
  }

  if (!ejemplares.length) {
    return (
      <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        No hay bibliotecas con ejemplares registrados para este título.
        {opacUrl ? (
          <>
            {" "}
            <a
              href={opacUrl}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-sky-700 underline-offset-4 hover:underline"
            >
              Consulta el catálogo oficial
            </a>
            .
          </>
        ) : null}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 flex-1">
            <label
              htmlFor="codigo-postal-cercania"
              className="text-xs font-semibold uppercase tracking-wider text-slate-400"
            >
              Ordenar por cercanía
            </label>
            <select
              id="codigo-postal-cercania"
              value={selectedCp}
              onChange={handlePostalCodeChange}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            >
              <option value="">Orden alfabético</option>
              {POSTAL_CODES.map((postalCode) => (
                <option key={postalCode.codigo} value={postalCode.codigo}>
                  {postalCodeLabel(postalCode)}
                </option>
              ))}
            </select>
          </div>
          {selectedCp ? (
            <button
              type="button"
              onClick={clearPostalCode}
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Quitar
            </button>
          ) : null}
        </div>
        <p className="mt-2 text-xs text-slate-500" aria-live="polite">
          {noLocations
            ? "No hay datos de ubicación disponibles para estas bibliotecas; se muestra el orden alfabético."
            : reference
              ? `Ordenado por cercanía a ${postalCodeLabel(reference)}. Distancias aproximadas.`
              : unknownPostalCode
                ? "Código postal no reconocido; se muestra el orden alfabético."
                : "Orden alfabético. Elige un código postal para ordenar por cercanía."}
        </p>
        <p className="mt-2 text-xs text-slate-400">
          Centroides de códigos postales: {postalCodesData.fuente}. Licencia:{" "}
          {postalCodesData.licencia}.
        </p>
      </div>

      {sortedGroups.map((group) => {
        const distance =
          reference && group.point
            ? haversineKm(group.point, reference)
            : null;
        return (
          <section
            key={group.key}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card"
          >
            <header className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 bg-slate-50 px-5 py-3">
              <div>
                <h3 className="font-semibold text-ink">{group.biblioteca}</h3>
                {group.sucursal ? (
                  <p className="text-sm text-slate-500">{group.sucursal}</p>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {distance !== null ? (
                  <span className="text-xs font-semibold text-sky-700">
                    {formatDistance(distance)}
                  </span>
                ) : null}
                {opacUrl ? (
                  <a
                    href={opacUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-medium text-sky-700 underline-offset-4 hover:underline"
                  >
                    Consultar en el OPAC
                  </a>
                ) : null}
              </div>
            </header>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-5 py-2 font-semibold">Signatura</th>
                    <th className="px-5 py-2 font-semibold">Tipo</th>
                    <th className="px-5 py-2 font-semibold">Soporte</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {group.items.map((ejemplar) => (
                    <tr key={ejemplar.id}>
                      <td className="px-5 py-3 font-mono text-xs text-slate-700">
                        {ejemplar.signatura ?? "—"}
                        {ejemplar.localizacion ? (
                          <span className="ml-2 font-sans text-xs text-slate-400">
                            {ejemplar.localizacion}
                          </span>
                        ) : null}
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {ejemplar.tipo_ejemplar ?? "—"}
                      </td>
                      <td className="px-5 py-3">
                        {ejemplar.soporte ? (
                          <SupportBadge support={ejemplar.soporte} />
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
    </div>
  );
}
