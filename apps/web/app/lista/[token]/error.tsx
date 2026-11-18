"use client";

import Link from "next/link";

export default function ListaError({ reset }: { error: Error; reset: () => void }) {
  return (
    <section className="mx-auto max-w-2xl rounded-3xl border border-rose-200 bg-rose-50 p-10 text-center">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-rose-500">
        Lista compartida
      </p>
      <h1 className="mt-2 text-2xl font-black text-rose-900">No se pudo cargar la lista</h1>
      <p className="mt-2 text-sm leading-6 text-rose-800">
        Comprueba que la API está disponible y vuelve a intentarlo.
      </p>
      <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
        >
          Reintentar
        </button>
        <Link
          href="/buscar"
          className="rounded-xl border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-800"
        >
          Volver a la búsqueda
        </Link>
      </div>
    </section>
  );
}
