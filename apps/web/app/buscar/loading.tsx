import { SearchSkeleton } from "@/components/SearchSkeleton";

export default function Loading() {
  return (
    <div className="space-y-6" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">Cargando búsqueda…</span>
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card sm:p-5">
        <div className="h-12 animate-pulse rounded-xl bg-slate-100" />
      </section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-2">
          <div className="h-7 w-64 animate-pulse rounded bg-slate-200" />
          <div className="h-4 w-80 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="h-10 w-52 animate-pulse rounded-xl bg-slate-100" />
      </div>
      <SearchSkeleton />
    </div>
  );
}
