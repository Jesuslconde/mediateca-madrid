import { headers } from "next/headers";

import { API_URL } from "./api";
import type { components } from "./api-types";

type Schemas = components["schemas"];

export type Lista = Schemas["ListaOut"];
export type ListaItem = Schemas["ListaItemOut"];
export type ListaCreated = Schemas["ListaCreatedOut"];
export type ItemMutation = Schemas["ItemMutationOut"];

export class ListApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ListApiError";
    this.status = status;
  }
}

async function listFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new ListApiError(response.status, detail || response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function clientIpHeaders(): Promise<Record<string, string>> {
  const store = await headers();
  const forwarded = store.get("x-forwarded-for")?.split(",")[0]?.trim();
  const real = store.get("x-real-ip")?.trim();
  const ip = forwarded || real;
  return ip ? { "X-Client-IP": ip } : {};
}

export async function createList(): Promise<ListaCreated> {
  return listFetch<ListaCreated>("/api/lists", {
    method: "POST",
    headers: await clientIpHeaders(),
  });
}

export async function getList(token: string): Promise<Lista | null> {
  try {
    return await listFetch<Lista>(`/api/lists/${encodeURIComponent(token)}`);
  } catch (error) {
    if (error instanceof ListApiError && error.status === 404) return null;
    throw error;
  }
}

export async function addItem(token: string, recordId: string): Promise<ItemMutation> {
  return listFetch<ItemMutation>(`/api/lists/${encodeURIComponent(token)}/items`, {
    method: "POST",
    body: JSON.stringify({ record_id: recordId }),
  });
}

export async function removeItem(token: string, recordId: string): Promise<ItemMutation> {
  return listFetch<ItemMutation>(
    `/api/lists/${encodeURIComponent(token)}/items/${encodeURIComponent(recordId)}`,
    { method: "DELETE" },
  );
}

export async function renameList(token: string, titulo: string): Promise<Lista> {
  return listFetch<Lista>(`/api/lists/${encodeURIComponent(token)}`, {
    method: "PATCH",
    body: JSON.stringify({ titulo }),
  });
}
