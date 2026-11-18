"use client";

import { useEffect } from "react";

import { adoptListAction } from "@/app/actions/lists";

export function AdoptList({ token }: { token: string }) {
  useEffect(() => {
    void adoptListAction(token).catch(() => {});
  }, [token]);

  return null;
}
