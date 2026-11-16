export default function Loading() {
  return (
    <div className="space-y-8" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">Cargando ficha…</span>

      <div className="h-4 w-36 animate-pulse rounded bg-slate-200" />

      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 gap-4">
            <div className="h-60 w-40 flex-none animate-pulse rounded-xl bg-slate-200" />
            <div className="min-w-0 flex-1 space-y-3">
              <div className="flex gap-2">
                <div className="h-6 w-16 animate-pulse rounded-full bg-slate-100" />
                <div className="h-6 w-20 animate-pulse rounded-full bg-slate-100" />
              </div>
              <div className="h-9 w-3/4 animate-pulse rounded bg-slate-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-slate-100" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-slate-100" />
            </div>
          </div>
          <div className="h-20 w-40 animate-pulse rounded-2xl bg-slate-100" />
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-5 sm:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="space-y-2">
              <div className="h-3 w-16 animate-pulse rounded bg-slate-100" />
              <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
            </div>
          ))}
        </div>
      </header>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-8">
          {Array.from({ length: 2 }).map((_, index) => (
            <section
              key={index}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card"
            >
              <div className="h-5 w-32 animate-pulse rounded bg-slate-200" />
              <div className="mt-4 space-y-2">
                <div className="h-4 w-full animate-pulse rounded bg-slate-100" />
                <div className="h-4 w-5/6 animate-pulse rounded bg-slate-100" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-slate-100" />
              </div>
            </section>
          ))}
        </div>
        <div className="space-y-6">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="h-32 animate-pulse rounded-2xl border border-slate-200 bg-white shadow-card"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
