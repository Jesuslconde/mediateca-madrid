import type { Ejemplar } from "@/lib/api";

import { SupportBadge } from "./SupportBadge";

function groupByLibrary(ejemplares: Ejemplar[]): Map<string, Ejemplar[]> {
  const groups = new Map<string, Ejemplar[]>();
  for (const ejemplar of ejemplares) {
    const key = `${ejemplar.biblioteca}|||${ejemplar.sucursal ?? ""}`;
    const items = groups.get(key) ?? [];
    items.push(ejemplar);
    groups.set(key, items);
  }
  return new Map(
    [...groups.entries()].sort(([a], [b]) => a.localeCompare(b, "es")),
  );
}

export function LibrariesTable({
  ejemplares,
  opacUrl,
}: {
  ejemplares: Ejemplar[];
  opacUrl?: string | null;
}) {
  if (!ejemplares.length) {
    return (
      <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        No hay bibliotecas con ejemplares registrados para este título.
      </p>
    );
  }

  const groups = groupByLibrary(ejemplares);

  return (
    <div className="space-y-4">
      {[...groups.entries()].map(([key, items]) => {
        const [biblioteca, sucursal] = key.split("|||");
        return (
          <section
            key={key}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card"
          >
            <header className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 bg-slate-50 px-5 py-3">
              <div>
                <h3 className="font-semibold text-ink">{biblioteca}</h3>
                {sucursal ? <p className="text-sm text-slate-500">{sucursal}</p> : null}
              </div>
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
                  {items.map((ejemplar) => (
                    <tr key={ejemplar.id}>
                      <td className="px-5 py-3 font-mono text-xs text-slate-700">
                        {ejemplar.signatura ?? "—"}
                        {ejemplar.localizacion ? (
                          <span className="ml-2 font-sans text-xs text-slate-400">
                            {ejemplar.localizacion}
                          </span>
                        ) : null}
                      </td>
                      <td className="px-5 py-3 text-slate-600">{ejemplar.tipo_ejemplar ?? "—"}</td>
                      <td className="px-5 py-3">
                        {ejemplar.soporte ? <SupportBadge support={ejemplar.soporte} /> : "—"}
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
