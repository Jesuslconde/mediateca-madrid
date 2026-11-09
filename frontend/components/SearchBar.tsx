export function SearchBar({
  defaultValue = "",
  compact = false,
}: {
  defaultValue?: string;
  compact?: boolean;
}) {
  return (
    <form
      action="/buscar"
      method="get"
      className={`flex w-full items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-card ${
        compact ? "" : "sm:p-3"
      }`}
    >
      <label htmlFor="q" className="sr-only">
        Buscar en el catálogo
      </label>
      <input
        id="q"
        name="q"
        type="search"
        defaultValue={defaultValue}
        placeholder="Título, director, reparto, género..."
        className={`min-w-0 flex-1 rounded-xl border-0 bg-transparent px-3 text-ink outline-none placeholder:text-slate-400 focus:ring-0 ${
          compact ? "py-2 text-sm" : "py-3 text-base"
        }`}
      />
      <button
        type="submit"
        className={`rounded-xl bg-ink px-5 font-semibold text-white transition hover:bg-slate-700 ${
          compact ? "py-2 text-sm" : "py-3"
        }`}
      >
        Buscar
      </button>
    </form>
  );
}
