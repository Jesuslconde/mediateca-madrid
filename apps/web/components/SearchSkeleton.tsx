export function SearchSkeleton() {
  return (
    <div
      className="grid gap-8 lg:grid-cols-[360px_minmax(0,1fr)]"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="sr-only">Cargando resultados…</span>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="h-4 w-20 animate-pulse rounded bg-slate-200" />
        <div className="mt-6 space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="flex items-center justify-between gap-3">
              <div className="h-3.5 w-28 animate-pulse rounded bg-slate-200" />
              <div className="h-3.5 w-6 animate-pulse rounded bg-slate-100" />
            </div>
          ))}
        </div>
        <div className="mt-8 space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-10 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="h-4 w-40 animate-pulse rounded bg-slate-200" />
          <div className="h-4 w-24 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"
            >
              <div className="flex gap-4">
                <div className="h-40 w-28 flex-none animate-pulse rounded-xl bg-slate-200" />
                <div className="min-w-0 flex-1 space-y-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-slate-200" />
                  <div className="h-3.5 w-1/2 animate-pulse rounded bg-slate-100" />
                  <div className="flex gap-2">
                    <div className="h-5 w-16 animate-pulse rounded bg-slate-100" />
                    <div className="h-5 w-20 animate-pulse rounded bg-slate-100" />
                    <div className="h-5 w-14 animate-pulse rounded bg-slate-100" />
                  </div>
                  <div className="h-3.5 w-full animate-pulse rounded bg-slate-100" />
                  <div className="h-3.5 w-5/6 animate-pulse rounded bg-slate-100" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
