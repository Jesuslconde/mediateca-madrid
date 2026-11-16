export const SORT_VALUES = [
  "relevancia",
  "anio_desc",
  "anio_asc",
  "titulo_asc",
  "duracion_asc",
] as const;

export type SortValue = (typeof SORT_VALUES)[number];

export const SORT_LABELS: Record<SortValue, string> = {
  relevancia: "Relevancia",
  anio_desc: "Año (más reciente)",
  anio_asc: "Año (más antiguo)",
  titulo_asc: "Título (A-Z)",
  duracion_asc: "Duración (menor)",
};

export function parseSort(value: string | undefined): SortValue {
  return SORT_VALUES.includes(value as SortValue)
    ? (value as SortValue)
    : "relevancia";
}
