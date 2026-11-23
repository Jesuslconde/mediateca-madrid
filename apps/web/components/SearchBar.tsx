import Form from "next/form";

export type SearchField = "todo" | "titn";

export function SearchBar({
  defaultValue = "",
  campo = "todo",
  compact = false,
}: {
  defaultValue?: string;
  campo?: SearchField;
  compact?: boolean;
}) {
  return (
    <Form
      action="/buscar"
      className={`flex w-full flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-card ${
        compact ? "" : "sm:p-3"
      }`}
    >
      <label htmlFor="campo" className="sr-only">
        Campo de búsqueda
      </label>
      <select
        id="campo"
        name="campo"
        defaultValue={campo}
        className={`rounded-xl border border-slate-200 bg-slate-50 font-semibold text-ink outline-none ${
          compact ? "px-2 py-2 text-sm" : "px-3 py-3 text-base"
        }`}
      >
        <option value="todo">Todo</option>
        <option value="titn">TITN</option>
      </select>
      <label htmlFor="q" className="sr-only">
        Buscar en el catálogo
      </label>
      <input
        id="q"
        name="q"
        type="search"
        defaultValue={defaultValue}
        placeholder="Título, director, reparto, género o TITN..."
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
    </Form>
  );
}
