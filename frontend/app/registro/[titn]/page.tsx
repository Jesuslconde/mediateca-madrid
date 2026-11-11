import Link from "next/link";
import { notFound } from "next/navigation";

import { LibrariesTable } from "@/components/LibrariesTable";
import { SupportBadge } from "@/components/SupportBadge";
import { getRecord, type Persona } from "@/lib/api";
import { countryLabel, languageLabel } from "@/lib/labels";

export const dynamic = "force-dynamic";

function roleGroup(role: string): string {
  const normalized = role.toLowerCase();
  if (normalized.includes("director")) return "Dirección";
  if (normalized.includes("guion")) return "Guion";
  if (normalized.includes("actor") || normalized.includes("actriz")) return "Reparto";
  if (normalized.includes("productor")) return "Producción";
  if (normalized.includes("fotograf")) return "Fotografía";
  if (normalized.includes("compositor") || normalized.includes("música")) return "Música";
  return "Otros créditos";
}

const ROLE_ORDER = [
  "Dirección",
  "Guion",
  "Reparto",
  "Producción",
  "Fotografía",
  "Música",
  "Otros créditos",
];

function groupPeople(personas: Persona[]): [string, string[]][] {
  const groups = new Map<string, string[]>();
  for (const persona of personas) {
    const group = roleGroup(persona.rol);
    const names = groups.get(group) ?? [];
    if (!names.includes(persona.nombre)) names.push(persona.nombre);
    groups.set(group, names);
  }
  return [...groups.entries()].sort(
    ([a], [b]) => ROLE_ORDER.indexOf(a) - ROLE_ORDER.indexOf(b),
  );
}

function Meta({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-800">{value}</dd>
    </div>
  );
}

export default async function RecordPage({
  params,
}: {
  params: Promise<{ titn: string }>;
}) {
  const { titn } = await params;
  const record = await getRecord(titn).catch(() => null);
  if (!record) notFound();

  const people = groupPeople(record.personas);
  const countries = (record.paises_origen ?? []).map((code) => countryLabel(code) ?? code);
  const bibliotecas = new Set(record.ejemplares.map((ejemplar) => ejemplar.biblioteca)).size;
  const relevantNotes = Object.entries(record.notas).filter(
    ([key]) => key.startsWith("Nota") || key.startsWith("Depósito"),
  );

  return (
    <article className="space-y-8">
      <div>
        <Link
          href="/buscar"
          className="text-sm font-medium text-slate-500 underline-offset-4 hover:text-ink hover:underline"
        >
          ← Volver a la búsqueda
        </Link>
      </div>

      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              {record.soportes.map((support) => (
                <SupportBadge key={support} support={support} />
              ))}
            </div>
            <h1 className="mt-4 text-3xl font-black leading-tight text-ink sm:text-4xl">
              {record.titulo.replace(/\s*\/\s*$/, "")}
            </h1>
            {record.titulo_uniforme && record.titulo_uniforme !== record.titulo ? (
              <p className="mt-2 text-base text-slate-500">{record.titulo_uniforme}</p>
            ) : null}
            <p className="mt-3 text-sm text-slate-600">
              {[record.publicacion, record.anio].filter(Boolean).join(" · ")}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3 text-right text-xs text-slate-500">
            <p className="font-mono">TITN {record.titn}</p>
            {record.ean ? <p className="mt-1 font-mono">EAN {record.ean}</p> : null}
          </div>
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-5 sm:grid-cols-4">
          <Meta label="Año" value={record.anio} />
          <Meta label="Duración" value={record.duracion_min ? `${record.duracion_min} min` : null} />
          <Meta label="Idioma" value={languageLabel(record.idioma)} />
          <Meta label="País" value={countryLabel(record.pais)} />
          <Meta label="Países de origen" value={countries.length ? countries.join(", ") : null} />
          <Meta label="Edad" value={record.edad_recomendada} />
          <Meta label="Tipo" value={record.tipo_documento} />
          <Meta label="Soporte principal" value={record.soporte_principal} />
          <Meta label="Ejemplares" value={record.ejemplares.length} />
        </dl>
      </header>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-8">
          {record.sinopsis ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-lg font-bold text-ink">Sinopsis</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{record.sinopsis}</p>
            </section>
          ) : null}

          {people.length ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-lg font-bold text-ink">Créditos</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {people.map(([group, names]) => (
                  <div key={group}>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      {group}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{names.join(", ")}</p>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
            <h2 className="text-lg font-bold text-ink">Bibliotecas con ejemplares</h2>
            <p className="mb-4 mt-1 text-xs text-slate-400">
              {record.ejemplares.length} ejemplar{record.ejemplares.length === 1 ? "" : "es"} en{" "}
              {bibliotecas} biblioteca{bibliotecas === 1 ? "" : "s"}. Consulta el estado de
              préstamo en la ficha del OPAC.
            </p>
            <LibrariesTable ejemplares={record.ejemplares} opacUrl={record.source_url} />
          </section>

          {relevantNotes.length ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-lg font-bold text-ink">Notas</h2>
              <dl className="mt-3 space-y-3">
                {relevantNotes.map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      {label}
                    </dt>
                    <dd className="mt-0.5 text-sm leading-6 text-slate-700">{value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          ) : null}
        </div>

        <aside className="space-y-6">
          {record.generos.length || record.materias.length ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Géneros y materias
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {record.generos.map((genero) => (
                  <span
                    key={genero}
                    className="rounded-full bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700"
                  >
                    {genero}
                  </span>
                ))}
                {record.materias.map((materia) => (
                  <span
                    key={materia}
                    className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600"
                  >
                    {materia}
                  </span>
                ))}
              </div>
            </section>
          ) : null}

          {record.enlaces.length ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Enlaces externos
              </h2>
              <ul className="mt-3 space-y-2 text-sm">
                {record.enlaces.map((enlace) => (
                  <li key={enlace.url}>
                    <a
                      href={enlace.url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-sky-700 underline-offset-4 hover:underline"
                    >
                      {enlace.etiqueta ?? enlace.url}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-xs leading-5 text-slate-500">
            <p>
              Datos procedentes del catálogo público de las Bibliotecas de la Comunidad de
              Madrid. La disponibilidad puede cambiar; confirma en el OPAC oficial antes de
              desplazarte.
            </p>
            {record.source_url ? (
              <a
                href={record.source_url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-block font-medium text-slate-700 underline-offset-4 hover:underline"
              >
                Ver ficha original
              </a>
            ) : null}
          </section>
        </aside>
      </div>
    </article>
  );
}
