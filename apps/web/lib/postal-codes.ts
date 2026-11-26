import postalCodesData from "@/lib/codigos-postales.json";

export type PostalCode = {
  codigo: string;
  municipio: string | null;
  latitud: number;
  longitud: number;
};

export const POSTAL_CODES: PostalCode[] = postalCodesData.codigos as PostalCode[];

export const POSTAL_CODE_BY_CODE = new Map(
  POSTAL_CODES.map((postalCode) => [postalCode.codigo, postalCode]),
);

export const POSTAL_CODES_SOURCE = postalCodesData.fuente as string;
export const POSTAL_CODES_LICENSE = postalCodesData.licencia as string;

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export function searchPostalCodes(term: string, limit = 8): PostalCode[] {
  const trimmed = term.trim();
  if (!trimmed) return [];
  const digits = /^\d+$/.test(trimmed);
  const query = normalize(trimmed);
  const results: PostalCode[] = [];
  for (const postalCode of POSTAL_CODES) {
    if (digits) {
      if (postalCode.codigo.startsWith(trimmed)) results.push(postalCode);
    } else if (postalCode.municipio && normalize(postalCode.municipio).includes(query)) {
      results.push(postalCode);
    }
    if (results.length >= limit) break;
  }
  return results;
}

export function postalCodeLabel(postalCode: PostalCode): string {
  return postalCode.municipio
    ? `${postalCode.codigo} — ${postalCode.municipio}`
    : postalCode.codigo;
}
