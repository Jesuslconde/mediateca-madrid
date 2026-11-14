import type { Metadata } from "next";
import Link from "next/link";

import packageJson from "../package.json";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Mediateca Madrid",
    template: "%s · Mediateca Madrid",
  },
  description:
    "Portal alternativo para buscar vídeos, DVD y Blu-ray de las bibliotecas públicas de Madrid.",
  icons: [{ rel: "icon", url: "/favicon.svg" }],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="flex min-h-screen flex-col">
        <header className="border-b border-white/10 bg-ink text-white">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-sm font-black">
                M
              </span>
              <span>
                <span className="block text-sm font-bold uppercase tracking-[0.2em] text-white/90">
                  Mediateca
                </span>
                <span className="block text-xs text-white/60">Bibliotecas de Madrid</span>
              </span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link href="/buscar" className="rounded-lg px-3 py-2 hover:bg-white/10">
                Buscar
              </Link>
              <Link href="/buscar?soporte=DVD" className="rounded-lg px-3 py-2 hover:bg-white/10">
                DVD
              </Link>
              <Link
                href="/buscar?soporte=Blu-ray"
                className="rounded-lg px-3 py-2 hover:bg-white/10"
              >
                Blu-ray
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">{children}</main>

        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <p>
                Portal alternativo no oficial. Datos obtenidos del catálogo público de las
                Bibliotecas de la Comunidad de Madrid.
              </p>
              <p className="text-xs text-slate-400">
                Este producto usa la API de TMDB, pero no está avalado ni certificado por TMDB.{" "}
                <a
                  href="https://www.themoviedb.org/"
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-slate-600 underline-offset-4 hover:underline"
                >
                  themoviedb.org
                </a>
              </p>
            </div>
            <div className="flex flex-col items-start gap-2 sm:items-end">
              <span
                className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-500"
                title="Versión del portal desplegada"
              >
                Versión {packageJson.version}
              </span>
              <a
                href="https://gestiona.comunidad.madrid/biblio_publicas"
                target="_blank"
                rel="noreferrer"
                className="font-medium text-slate-700 underline-offset-4 hover:underline"
              >
                Ir al OPAC oficial
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
