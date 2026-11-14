import Link from "next/link";

import { SearchBar } from "@/components/SearchBar";
import { getStats, type Stats } from "@/lib/api";

export const dynamic = "force-dynamic";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-black text-ink">{value}</p>
    </div>
  );
}

export default async function HomePage() {
  let stats: Stats | null = null;
  try {
    stats = await getStats();
  } catch {
    stats = null;
  }

  return (
    <div className="space-y-12">
      <section className="overflow-hidden rounded-3xl bg-ink px-6 py-12 text-white shadow-card sm:px-10">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-300">
            Catálogo alternativo
          </p>
          <h1 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
            Encuentra cine en las bibliotecas de Madrid.
            <span className="text-rose-300"> Y filtra por DVD o Blu-ray.</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Busca por título, dirección, reparto o género y consulta qué bibliotecas tienen
            cada ejemplar. Sin las limitaciones del OPAC.
          </p>
          <div className="mx-auto mt-8 max-w-2xl">
            <SearchBar />
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-sm">
            <Link
              href="/buscar?soporte=DVD"
              className="rounded-full border border-white/20 px-4 py-2 font-semibold text-white transition hover:bg-white/10"
            >
              Solo DVD
            </Link>
            <Link
              href="/buscar?soporte=Blu-ray"
              className="rounded-full border border-white/20 px-4 py-2 font-semibold text-white transition hover:bg-white/10"
            >
              Solo Blu-ray
            </Link>
          </div>
        </div>
      </section>

      {stats ? (
        <section className="grid grid-cols-3 gap-3">
          <StatCard label="Ediciones" value={stats.ediciones.toLocaleString("es-ES")} />
          <StatCard label="Ejemplares" value={stats.ejemplares.toLocaleString("es-ES")} />
          <StatCard label="Bibliotecas" value={stats.bibliotecas.toLocaleString("es-ES")} />
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink">DVD y Blu-ray por separado</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            El OPAC los agrupa bajo “Videos y DVD”. Aquí se detectan desde la descripción
            física y el soporte de cada ejemplar.
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink">Dirección, reparto y guion</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Los créditos del registro se normalizan y se pueden usar como criterio de
            búsqueda, junto con género, año, idioma y duración.
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink">Bibliotecas y signaturas</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Cada ficha muestra las bibliotecas y sucursales con ejemplares, su signatura, tipo
            y soporte, con enlace a la ficha del OPAC para consultar el préstamo.
          </p>
        </article>
      </section>

      {stats && Object.keys(stats.por_soporte).length ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink">Reparto por soporte</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(stats.por_soporte).map(([support, count]) => (
              <Link
                key={support}
                href={`/buscar?soporte=${encodeURIComponent(support)}`}
                className="rounded-xl border border-slate-200 px-4 py-3 text-sm transition hover:border-slate-300 hover:bg-slate-50"
              >
                <span className="block font-semibold text-ink">{support}</span>
                <span className="text-slate-500">{count.toLocaleString("es-ES")} ediciones</span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
