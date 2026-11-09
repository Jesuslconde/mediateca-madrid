const STYLES: Record<string, string> = {
  DVD: "border-sky-200 bg-sky-50 text-sky-800",
  "Blu-ray": "border-indigo-200 bg-indigo-50 text-indigo-800",
  "4K UHD": "border-purple-200 bg-purple-50 text-purple-800",
  VHS: "border-amber-200 bg-amber-50 text-amber-800",
  Varios: "border-slate-200 bg-slate-100 text-slate-700",
};

export function SupportBadge({ support }: { support: string }) {
  const style = STYLES[support] ?? "border-slate-200 bg-slate-100 text-slate-700";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style}`}
    >
      {support}
    </span>
  );
}
