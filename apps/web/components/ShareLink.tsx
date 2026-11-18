"use client";

import { useEffect, useState } from "react";

export function ShareLink({ path }: { path: string }) {
  const [origin, setOrigin] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  const url = `${origin}${path}`;

  async function copy() {
    setError(false);
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setError(true);
    }
  }

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">
        Enlace compartible
      </p>
      <p className="mt-1 text-xs leading-5 text-amber-800">
        Cualquiera que tenga este enlace puede ver y editar la lista. No lo publiques si no
        quieres que otros puedan cambiarla.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input
          readOnly
          value={url}
          onFocus={(event) => event.currentTarget.select()}
          aria-label="Enlace compartible de la lista"
          className="min-w-0 flex-1 rounded-xl border border-amber-200 bg-white px-3 py-2 font-mono text-xs text-ink outline-none focus:border-amber-400"
        />
        <button
          type="button"
          onClick={copy}
          className="rounded-xl bg-ink px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-700"
        >
          {copied ? "Copiado" : "Copiar enlace"}
        </button>
      </div>
      {error ? (
        <p role="status" className="mt-2 text-xs text-rose-700">
          No se pudo copiar automáticamente. Selecciona el texto y cópialo a mano.
        </p>
      ) : null}
    </div>
  );
}
