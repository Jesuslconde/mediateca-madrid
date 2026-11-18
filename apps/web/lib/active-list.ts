import { getActiveListToken } from "./list-cookie";
import { getList, type Lista } from "./lists";

export async function getActiveList(): Promise<Lista | null> {
  const token = await getActiveListToken();
  if (!token) return null;
  try {
    return await getList(token);
  } catch {
    return null;
  }
}

export function savedRecordIds(lista: Lista | null): Set<string> {
  return new Set((lista?.items ?? []).map((item) => item.record_id));
}

export const savedTitns = savedRecordIds;
