import type { components } from "./api-types";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

type Schemas = components["schemas"];

export type SearchHit = Schemas["SearchHit"];
export type SearchResponse = Schemas["SearchResponse"];
export type Library = Schemas["LibraryOut"];
export type Stats = Schemas["StatsResponse"];
export type Persona = Schemas["PersonaOut"];
export type Enlace = Schemas["EnlaceOut"];
export type Ejemplar = Schemas["EjemplarOut"];
export type Obra = Schemas["ObraOut"];
export type RecordDetail = Schemas["RecordDetail"];

export type SearchParamsInput = {
  q?: string;
  soporte?: string[];
  genero?: string;
  anio_desde?: number;
  anio_hasta?: number;
  idioma?: string;
  paises_origen?: string[];
  biblioteca?: string;
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
