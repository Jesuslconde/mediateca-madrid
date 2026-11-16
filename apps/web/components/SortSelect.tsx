"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition, type ChangeEvent } from "react";

import { SORT_LABELS, SORT_VALUES, type SortValue } from "@/lib/sort";

export function SortSelect({ value }: { value: SortValue }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort", event.target.value);
    params.delete("page");
    startTransition(() => {
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    });
  }

  return (
    <label className="flex items-center gap-2 text-sm text-slate-500">
      <span className="font-medium">Ordenar por</span>
      <select
        value={value}
        onChange={handleChange}
        disabled={isPending}
        aria-busy={isPending}
        className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-ink disabled:opacity-60"
      >
        {SORT_VALUES.map((sort) => (
          <option key={sort} value={sort}>
            {SORT_LABELS[sort]}
          </option>
        ))}
      </select>
      {isPending ? (
        <span className="text-xs text-slate-400" aria-live="polite">
          Actualizando…
        </span>
      ) : null}
    </label>
  );
}
