"use client";

import { useSyncExternalStore } from "react";

const STORAGE_KEY = "mediateca:codigo-postal";

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

function getSnapshot() {
  return window.localStorage.getItem(STORAGE_KEY) ?? "";
}

function getServerSnapshot() {
  return "";
}

function notify() {
  for (const listener of listeners) {
    listener();
  }
}

export function setPostalCode(value: string) {
  if (value) {
    window.localStorage.setItem(STORAGE_KEY, value);
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  notify();
}

export function clearPostalCode() {
  window.localStorage.removeItem(STORAGE_KEY);
  notify();
}

export function usePostalCode(): string {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
