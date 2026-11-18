import Link from "next/link";

export default function ListaNotFound() {
  return (
    <section className="mx-auto max-w-2xl rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-card">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
        Lista compartida
      </p>
      <h1 className="mt-2 text-2xl font-black text-ink">Esta lista no existe</h1>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        El enlace puede estar incompleto o la lista puede haber caducado por falta de uso.
      </p>
      <Link
        href="/buscar"
        className="mt-5 inline-block rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
      >
        Volver a la búsqueda
      </Link>
    </section>
  );
}
