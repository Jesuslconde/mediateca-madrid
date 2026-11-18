import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { AdoptList } from "@/components/AdoptList";
import { ListaView } from "@/components/ListaView";
import { getActiveListToken } from "@/lib/list-cookie";
import { getList } from "@/lib/lists";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Lista compartida",
  robots: { index: false, follow: false },
};

export default async function ListaPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const lista = await getList(token);
  if (!lista) notFound();

  const activeToken = await getActiveListToken();

  return (
    <>
      {activeToken !== token ? <AdoptList token={token} /> : null}
      <ListaView lista={lista} token={token} />
    </>
  );
}
