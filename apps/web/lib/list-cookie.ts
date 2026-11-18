import { cookies } from "next/headers";

export const LIST_COOKIE = "mediateca_lista";
export const LIST_COOKIE_MAX_AGE = 60 * 60 * 24 * 180;

export async function getActiveListToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(LIST_COOKIE)?.value ?? null;
}

export async function setActiveListToken(token: string): Promise<void> {
  const store = await cookies();
  store.set(LIST_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: LIST_COOKIE_MAX_AGE,
  });
}

export async function clearActiveListToken(): Promise<void> {
  const store = await cookies();
  store.delete(LIST_COOKIE);
}
