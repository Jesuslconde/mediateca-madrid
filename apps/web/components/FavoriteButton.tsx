"use client";

import { useOptimistic, useState, useTransition, type FormEvent } from "react";

import { toggleFavoriteAction, toggleFavoriteFormAction } from "@/app/actions/lists";

export function FavoriteButton({
  titn,
  saved: initialSaved,
  compact = true,
}: {
  titn: string;
  saved: boolean;
  compact?: boolean;
}) {
  const [saved, setSaved] = useState(initialSaved);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [optimisticSaved, setOptimisticSaved] = useOptimistic(
    saved,
    (_current, next: boolean) => next,
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const previous = saved;
    setError(null);
    startTransition(async () => {
      setOptimisticSaved(!previous);
      const result = await toggleFavoriteAction(titn, previous);
      if (result.error) {
        setError(result.error);
        return;
      }
      setSaved(result.saved);
    });
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <form action={toggleFavoriteFormAction} onSubmit={onSubmit}>
        <input type="hidden" name="titn" value={titn} />
        <input type="hidden" name="saved" value={String(saved)} />
        <button
          type="submit"
          aria-pressed={optimisticSaved}
          aria-label={optimisticSaved ? "Quitar de Mi lista" : "Guardar en Mi lista"}
          title={optimisticSaved ? "Quitar de Mi lista" : "Guardar en Mi lista"}
          disabled={isPending}
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition ${
            optimisticSaved
              ? "border-rose-200 bg-rose-50 text-accent"
              : "border-slate-200 bg-white text-slate-500 hover:border-rose-200 hover:text-accent"
          } ${isPending ? "cursor-wait opacity-70" : ""}`}
        >
          <HeartIcon filled={optimisticSaved} />
          <span className={compact ? "sr-only" : ""}>
            {optimisticSaved ? "Guardado" : "Guardar"}
          </span>
        </button>
      </form>
      {error ? (
        <p role="status" className="max-w-48 text-right text-[11px] leading-4 text-rose-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1L12 21l7.7-7.6 1.1-1a5.5 5.5 0 0 0 0-7.8Z" />
    </svg>
  );
}
