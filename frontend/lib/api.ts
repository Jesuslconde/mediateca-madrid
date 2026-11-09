const API_URL = process.env.API_URL ?? "http://localhost:8000";

export type SearchHit = {
  id: string;
  titn: string;
  titulo: string;
  titulo_uniforme?: string | null;
  publicacion?: string | null;
  anio?: number | null;
  idioma?: string | null;
  pais?: string | null;
  duracion_min?: number | null;
  edad_recomendada?: string | null;
  sinopsis?: string | null;
  generos?: string[];
  materias?: string[];
  soportes?: string[];
  soporte_principal?: string | null;
  bibliotecas?: string[];
  disponible?: boolean;
  ejemplares?: number;
  directores?: string[];
  actores?: string[];
  guionistas?: string[];
  _formatted?: {
    titulo?: string;
    sinopsis?: string;
  };
};

export type SearchResponse = {
  query: string;
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  took_ms: number;
  facets: Record<string, Record<string, number>>;
  hits: SearchHit[];
};

export type Library = {
  codigo: string;
  nombre: string;
  municipio: string | null;
  ejemplares: number;
  disponibles: number;
};

export type Stats = {
  ediciones: number;
  ejemplares: number;
  disponibles: number;
  bibliotecas: number;
  por_soporte: Record<string, number>;
};

export type Persona = {
  nombre: string;
  rol: string;
};

export type Enlace = {
  url: string;
  etiqueta: string | null;
};

export type Ejemplar = {
  id: number;
  biblioteca: string;
  biblioteca_codigo: string;
  sucursal: string | null;
  sucursal_codigo: string | null;
  localizacion: string | null;
  signatura: string | null;
  tipo_ejemplar: string | null;
  soporte: string | null;
  estado: string | null;
  disponible: boolean;
};

export type Obra = {
  id: number;
  titulo_uniforme: string;
  anio: number | null;
  director_principal: string | null;
};

export type RecordDetail = {
  titn: string;
  titulo: string;
  titulo_uniforme: string | null;
  publicacion: string | null;
  anio: number | null;
  idioma: string | null;
  pais: string | null;
  duracion_min: number | null;
  edad_recomendada: string | null;
  sinopsis: string | null;
  generos: string[];
  materias: string[];
  soportes: string[];
  soporte_principal: string | null;
  ean: string | null;
  tipo_documento: string | null;
  disponible: boolean | null;
  personas: Persona[];
  enlaces: Enlace[];
  ejemplares: Ejemplar[];
  obra: Obra | null;
  notas: Record<string, string>;
  marc: Record<string, unknown>;
  source_url: string | null;
  updated_at: string | null;
};

export type SearchParamsInput = {
  q?: string;
  soporte?: string[];
  genero?: string;
  anio_desde?: number;
  anio_hasta?: number;
  idioma?: string;
  biblioteca?: string;
  disponible?: boolean;
  page?: number;
  limit?: number;
  sort?: string;
};

function queryString(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null && item !== "") {
          search.append(key, String(item));
        }
      }
    } else {
      search.set(key, String(value));
    }
  }
  return search.toString();
}

async function apiFetch<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const qs = params ? queryString(params) : "";
  const url = `${API_URL}${path}${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${detail || response.statusText}`);
  }
  return (await response.json()) as T;
}

export function searchRecords(params: SearchParamsInput): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/api/search", params as Record<string, unknown>);
}

export function getRecord(titn: string): Promise<RecordDetail> {
  return apiFetch<RecordDetail>(`/api/records/${encodeURIComponent(titn)}`);
}

export function getLibraries(): Promise<Library[]> {
  return apiFetch<Library[]>("/api/libraries");
}

export function getStats(): Promise<Stats> {
  return apiFetch<Stats>("/api/stats");
}
