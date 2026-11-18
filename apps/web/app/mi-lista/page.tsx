import type { Metadata } from "next";
import Link from "next/link";

import { createListAction } from "@/app/actions/lists";
import { ListaView } from "@/components/ListaView";
import { getActiveListToken } from "@/lib/list-cookie";
import { getList } from "@/lib/lists";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Mi lista",
  robots: { index: false, follow: false },
};

export default async function MiListaPage() {
  const token = await getActiveListToken();
  let lista = null;
  let failed = false;

  if (token) {
    try {
      lista = await getList(token);
    } catch {
      failed = true;
    }
  }

  if (failed) {
    return (
      <section className="rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
        <h1 className="text-xl font-bold text-rose-900">No se pudo cargar la lista</h1>
        <p className="mt-2 text-sm text-rose-800">
          Comprueba que la API está disponible y vuelve a intentarlo.
        </p>
        <Link
          href="/mi-lista"
          className="mt-4 inline-block rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
        >
          Reintentar
        </Link>
      </section>
    );
  }

  if (!token || !lista) {
    return (
      <section className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-card">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
          Lista de favoritos
        </p>
        <h1 className="mt-2 text-2xl font-black text-ink">Todavía no tienes una lista</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
          Guarda títulos con el corazón desde la búsqueda o desde una ficha. También puedes
          crear una lista vacía y compartir su enlace.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <form action={createListAction}>
            <button
              type="submit"
              className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              Crear mi lista
            </button>
          </form>
          <Link
            href="/buscar"
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-ink"
          >
            Buscar títulos
          </Link>
        </div>
      </section>
    );
  }

  return <ListaView lista={lista} token={token} />;
}
