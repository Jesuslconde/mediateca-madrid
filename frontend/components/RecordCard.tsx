import Link from "next/link";

import type { SearchHit } from "@/lib/api";
import { countryLabel, languageLabel } from "@/lib/labels";

import { SupportBadge } from "./SupportBadge";

function Meta({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
      <span className="font-medium text-slate-500">{label}</span>
      <span>{value}</span>
    </span>
  );
}

export function RecordCard({ hit }: { hit: SearchHit }) {
  const title = hit._formatted?.titulo ?? hit.titulo;
  const synopsis = hit._formatted?.sinopsis ?? hit.sinopsis;
  const countries = (hit.paises_origen ?? []).map((code) => countryLabel(code) ?? code);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-slate-300">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href={`/registro/${hit.titn}`}
            className="text-lg font-bold leading-tight text-ink underline-offset-4 hover:text-accent hover:underline"
          >
            <span dangerouslySetInnerHTML={{ __html: title }} />
          </Link>
          {hit.titulo_uniforme && hit.titulo_uniforme !== hit.titulo ? (
            <p className="mt-1 text-sm text-slate-500">{hit.titulo_uniforme}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(hit.soportes ?? []).map((soporte) => (
            <SupportBadge key={soporte} support={soporte} />
          ))}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <Meta label="Año" value={hit.anio} />
        <Meta label="Duración" value={hit.duracion_min ? `${hit.duracion_min} min` : null} />
        <Meta label="Idioma" value={languageLabel(hit.idioma)} />
        <Meta label="Origen" value={countries.length ? countries.join(", ") : null} />
        <Meta label="Edad" value={hit.edad_recomendada} />
      </div>

      {synopsis ? (
        <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">
          <span dangerouslySetInnerHTML={{ __html: synopsis }} />
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {(hit.generos ?? []).slice(0, 3).map((genero) => (
          <span key={genero} className="rounded-full bg-rose-50 px-2 py-0.5 text-rose-700">
            {genero}
          </span>
        ))}
        {hit.directores?.length ? <span>Dir. {hit.directores.join(", ")}</span> : null}
        {hit.actores?.length ? (
          <span className="truncate">Reparto: {hit.actores.slice(0, 4).join(", ")}</span>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-sm">
        <span className="text-slate-600">
          {hit.ejemplares ?? 0} ejemplar{hit.ejemplares === 1 ? "" : "es"}
        </span>
        {hit.bibliotecas?.length ? (
          <span className="text-xs text-slate-500">
            {hit.bibliotecas.length} biblioteca{hit.bibliotecas.length === 1 ? "" : "s"}
          </span>
        ) : null}
      </div>
    </article>
  );
}
