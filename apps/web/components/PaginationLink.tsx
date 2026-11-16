"use client";

import Link, { useLinkStatus } from "next/link";
import type { ReactNode } from "react";

function PendingIndicator() {
  const { pending } = useLinkStatus();
  if (!pending) return null;
  return (
    <span className="ml-2 text-xs text-slate-400" aria-live="polite">
      Cargando…
    </span>
  );
}

export function PaginationLink({
  href,
  children,
}: {
  href?: string;
  children: ReactNode;
}) {
  const base = "rounded-xl border px-4 py-2 text-sm font-medium";

  if (!href) {
    return (
      <span className={`${base} border-slate-100 text-slate-300`}>{children}</span>
    );
  }

  return (
    <Link
      href={href}
      className={`${base} border-slate-200 bg-white text-slate-700 hover:bg-slate-50`}
    >
      {children}
      <PendingIndicator />
    </Link>
  );
}
