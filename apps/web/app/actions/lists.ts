"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { getActiveListToken, setActiveListToken } from "@/lib/list-cookie";
import {
  addItem,
  createList,
  ListApiError,
  removeItem,
  renameList,
} from "@/lib/lists";

export type FavoriteResult = {
  saved: boolean;
  itemCount: number;
  error?: string;
};

function refresh() {
  revalidatePath("/", "layout");
}

async function ensureListToken(): Promise<string> {
  const current = await getActiveListToken();
  if (current) return current;
  const created = await createList();
  await setActiveListToken(created.token);
  return created.token;
}

export async function createListAction(): Promise<void> {
  const created = await createList();
  await setActiveListToken(created.token);
  refresh();
  redirect("/mi-lista");
}

export async function toggleFavoriteAction(
  titn: string,
  saved: boolean,
): Promise<FavoriteResult> {
  try {
    let token = await ensureListToken();
    try {
      const result = saved ? await removeItem(token, titn) : await addItem(token, titn);
      refresh();
      return { saved: !saved, itemCount: result.item_count };
    } catch (error) {
      if (error instanceof ListApiError && error.status === 404) {
        const created = await createList();
        token = created.token;
        await setActiveListToken(token);
        const result = saved ? await removeItem(token, titn) : await addItem(token, titn);
        refresh();
        return { saved: !saved, itemCount: result.item_count };
      }
      throw error;
    }
  } catch (error) {
    if (error instanceof ListApiError && error.status === 409) {
      return {
        saved,
        itemCount: -1,
        error: "La lista está llena. Quita algún título antes de añadir otro.",
      };
    }
    return {
      saved,
      itemCount: -1,
      error: "No se pudo actualizar la lista. Inténtalo de nuevo.",
    };
  }
}

export async function toggleFavoriteFormAction(formData: FormData): Promise<void> {
  const titn = String(formData.get("titn") ?? "").trim();
  if (!titn) return;
  const saved = formData.get("saved") === "true";
  await toggleFavoriteAction(titn, saved);
}

export async function removeItemAction(formData: FormData): Promise<void> {
  const token = String(formData.get("token") ?? "").trim();
  const titn = String(formData.get("titn") ?? "").trim();
  if (!token || !titn) return;
  try {
    await removeItem(token, titn);
  } catch {
    // La lista puede haber caducado; la pagina se refresca igualmente.
  }
  refresh();
}

export async function renameListAction(formData: FormData): Promise<void> {
  const token = String(formData.get("token") ?? "").trim();
  if (!token) return;
  try {
    await renameList(token, String(formData.get("titulo") ?? ""));
  } catch {
    // La lista puede haber caducado; la pagina se refresca igualmente.
  }
  refresh();
}

export async function adoptListAction(token: string): Promise<void> {
  if (!token) return;
  await setActiveListToken(token);
  refresh();
}
