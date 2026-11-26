"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import {
  POSTAL_CODE_BY_CODE,
  postalCodeLabel,
  searchPostalCodes,
} from "@/lib/postal-codes";
import {
  clearPostalCode,
  setPostalCode,
  usePostalCode,
} from "@/lib/use-postal-code";

export function GlobalPostalCode({
  variant = "header",
}: {
  variant?: "header" | "card";
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const stored = usePostalCode();

  const isSearch = pathname === "/buscar";
  const urlCp = isSearch ? (searchParams.get("cp") ?? "") : "";
  const value = urlCp || stored;

  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);

  const boxClass =
    variant === "header"
      ? "bg-white/10 focus-within:ring-accent"
      : "border border-slate-200 bg-white focus-within:ring-ink";
  const inputClass =
    variant === "header"
      ? "text-white placeholder:text-white/50"
      : "text-ink placeholder:text-slate-400";
  const clearClass =
    variant === "header"
      ? "text-white/70 hover:bg-white/10 hover:text-white"
      : "text-slate-500 hover:bg-slate-100 hover:text-ink";

  useEffect(() => {
    if (value) {
      const postalCode = POSTAL_CODE_BY_CODE.get(value);
      setTerm(postalCode ? postalCodeLabel(postalCode) : value);
    } else {
      setTerm("");
    }
  }, [value]);

  const suggestions = useMemo(() => searchPostalCodes(term), [term]);

  function replaceQuery(next: URLSearchParams) {
    next.delete("page");
    const query = next.toString();
    router.replace(query ? `/buscar?${query}` : "/buscar");
  }

  function select(codigo: string) {
    setPostalCode(codigo);
    setOpen(false);
    if (isSearch) {
      const next = new URLSearchParams(searchParams.toString());
      next.set("cp", codigo);
      replaceQuery(next);
    }
  }

  function clear() {
    clearPostalCode();
    setOpen(false);
    if (isSearch) {
      const next = new URLSearchParams(searchParams.toString());
      next.delete("cp");
      next.delete("radio_km");
      next.delete("excluir");
      replaceQuery(next);
    }
  }

  const hasValue = Boolean(value);

  return (
    <div className="relative">
      <label htmlFor="global-cp" className="sr-only">
        Código postal de referencia
      </label>
      <div
        className={`flex items-center gap-1 rounded-lg px-2 py-1.5 focus-within:ring-2 ${boxClass}`}
      >
        <input
          id="global-cp"
          type="search"
          value={term}
          onChange={(event) => {
            setTerm(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="Código postal"
          autoComplete="off"
          className={`w-28 bg-transparent text-sm focus:outline-none ${inputClass}`}
        />
        {hasValue ? (
          <button
            type="button"
            onClick={clear}
            aria-label="Quitar código postal"
            className={`grid h-5 w-5 place-items-center rounded-full ${clearClass}`}
          >
            ×
          </button>
        ) : null}
      </div>

      {open && suggestions.length > 0 ? (
        <ul className="absolute right-0 z-20 mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 text-sm text-ink shadow-lg">
          {suggestions.map((postalCode) => (
            <li key={postalCode.codigo}>
              <button
                type="button"
                onMouseDown={(event) => {
                  event.preventDefault();
                  select(postalCode.codigo);
                }}
                className="block w-full px-3 py-2 text-left hover:bg-slate-100"
              >
                {postalCodeLabel(postalCode)}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
