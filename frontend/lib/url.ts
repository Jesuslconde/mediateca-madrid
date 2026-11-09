export type RawSearchParams = Record<string, string | string[] | undefined>;

export function first(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value[0];
  return value;
}

export function toArray(value: string | string[] | undefined): string[] {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

export function buildSearchQuery(
  params: RawSearchParams,
  overrides: Record<string, string | string[] | undefined | null> = {},
): string {
  const merged: Record<string, string | string[] | undefined | null> = {
    ...params,
    ...overrides,
  };
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(merged)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item) search.append(key, item);
      }
    } else {
      search.set(key, value);
    }
  }
  return search.toString();
}
