// SPDX-License-Identifier: Apache-2.0
const STATUS_COLORS: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-400",
  reserved: "bg-amber-500/15 text-amber-400",
  container: "bg-sky-500/15 text-sky-400",
  deprecated: "bg-red-500/15 text-red-400",
};

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "bg-zinc-500/15 text-zinc-400";
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs ${color}`}>{status}</span>
  );
}
