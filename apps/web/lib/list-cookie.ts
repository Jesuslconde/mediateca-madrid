import { cookies, headers } from "next/headers";

import { parseCookieSecureMode, shouldSecureCookie } from "./list-cookie-config";

export const LIST_COOKIE = "mediateca_lista";
export const LIST_COOKIE_MAX_AGE = 60 * 60 * 24 * 180;

async function resolveSecureCookie(): Promise<boolean> {
  const mode = parseCookieSecureMode(process.env.MEDITECA_WEB_COOKIE_SECURE);
  if (mode !== "auto") return shouldSecureCookie(mode, null);
  const store = await headers();
  return shouldSecureCookie("auto", store.get("x-forwarded-proto"));
}

export async function getActiveListToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(LIST_COOKIE)?.value ?? null;
}

export async function setActiveListToken(token: string): Promise<void> {
  const store = await cookies();
  store.set(LIST_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: await resolveSecureCookie(),
    path: "/",
    maxAge: LIST_COOKIE_MAX_AGE,
  });
}

export async function clearActiveListToken(): Promise<void> {
  const store = await cookies();
  store.delete(LIST_COOKIE);
}
