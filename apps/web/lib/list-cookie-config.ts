export type CookieSecureMode = "auto" | "true" | "false";

export function parseCookieSecureMode(value: string | undefined): CookieSecureMode {
  const normalized = (value ?? "").trim().toLowerCase();
  if (normalized === "true" || normalized === "false") return normalized;
  return "auto";
}

export function shouldSecureCookie(
  mode: CookieSecureMode,
  forwardedProto: string | null,
): boolean {
  if (mode === "true") return true;
  if (mode === "false") return false;
  const proto = forwardedProto?.split(",")[0]?.trim().toLowerCase();
  return proto === "https";
}
