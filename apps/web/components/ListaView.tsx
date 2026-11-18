import Link from "next/link";

import { removeItemAction, renameListAction } from "@/app/actions/lists";
import type { Lista } from "@/lib/lists";

import { ShareLink } from "./ShareLink";
import { SupportBadge } from "./SupportBadge";

export function ListaView({ lista, token }: { lista: Lista; token: string }) {
  const count = lista.items.length;

  return (
    <article className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
              Lista de favoritos
            </p>
            <h1 className="mt-2 text-3xl font-black leading-tight text-ink sm:text-4xl">
              {lista.titulo}
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              {count} título{count === 1 ? "" : "s"}
            </p>
          </div>

          <form action={renameListAction} className="flex flex-wrap items-center gap-2">
            <input type="hidden" name="token" value={token} />
            <label htmlFor="titulo-lista" className="sr-only">
              Nombre de la lista
            </label>
            <input
              id="titulo-lista"
              name="titulo"
              defaultValue={lista.titulo}
              maxLength={80}
              className="w-56 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-slate-400"
            />
            <button
              type="submit"
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-ink"
            >
              Renombrar
            </button>
          </form>
        </div>

        <div className="mt-5">
          <ShareLink path={`/lista/${token}`} />
        </div>
      </header>

      {count === 0 ? (
        <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-lg font-bold text-ink">Esta lista está vacía</p>
          <p className="mt-2 text-sm text-slate-500">
            Busca títulos en el catálogo y pulsa el corazón para guardarlos aquí.
          </p>
          <Link
            href="/buscar"
            className="mt-4 inline-block rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
          >
            Ir a la búsqueda
          </Link>
        </section>
      ) : (
        <ul className="space-y-3">
          {lista.items.map((item) => (
            <li
              key={item.titn}
              className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card transition hover:border-slate-300"
            >
              <div className="flex gap-4">
                {item.poster_url ? (
                  <img
                    src={item.poster_url}
                    alt={`Portada de ${item.titulo}`}
                    width={64}
                    height={96}
                    loading="lazy"
                    className="h-24 w-16 flex-none rounded-xl bg-slate-100 object-cover"
                  />
                ) : null}

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      {item.disponible ? (
                        <Link
                          href={`/registro/${item.titn}`}
                          className="text-base font-bold leading-tight text-ink underline-offset-4 hover:text-accent hover:underline"
                        >
                          {item.titulo}
                        </Link>
                      ) : (
                        <span className="text-base font-bold leading-tight text-slate-500">
                          {item.titulo}
                        </span>
                      )}
                      {!item.disponible ? (
                        <span className="ml-2 inline-flex rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                          Ficha no disponible
                        </span>
                      ) : null}
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        {item.anio ? (
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                            {item.anio}
                          </span>
                        ) : null}
                        {item.soportes.map((soporte) => (
                          <SupportBadge key={soporte} support={soporte} />
                        ))}
                      </div>
                    </div>

                    <form action={removeItemAction}>
                      <input type="hidden" name="token" value={token} />
                      <input type="hidden" name="titn" value={item.titn} />
                      <button
                        type="submit"
                        className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-500 transition hover:border-rose-200 hover:text-accent"
                      >
                        Quitar
                      </button>
                    </form>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-3 text-xs">
                    {item.disponible ? (
                      <Link
                        href={`/registro/${item.titn}`}
                        className="font-medium text-slate-600 underline-offset-4 hover:text-ink hover:underline"
                      >
                        Ver ficha
                      </Link>
                    ) : null}
                    {item.opac_url ? (
                      <a
                        href={item.opac_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-sky-700 underline-offset-4 hover:underline"
                      >
                        Ver en el OPAC
                      </a>
                    ) : null}
                    {!item.disponible ? (
                      <span className="text-slate-400">
                        La ficha ya no está en el catálogo; puedes quitar el título.
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
