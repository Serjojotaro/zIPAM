// SPDX-License-Identifier: Apache-2.0
// §23 address grid: every address of a small prefix as a cell colored by
// status. Renders only when the whole range fits in GRID_MAX cells (§62).
import type { IPAddress } from "../../api/types";
import { enumerateNetwork, parseCidr } from "../ipam/iptools";

export const GRID_MAX = 1024;

const STATUS_BG: Record<string, string> = {
  active: "bg-emerald-600 text-white",
  reserved: "bg-amber-600 text-black",
  deprecated: "bg-red-600 text-white",
};

interface AddressGridProps {
  cidr: string;
  addresses: IPAddress[];
  onCellClick: (address: string, existing: IPAddress | null) => void;
}

export function AddressGrid({ cidr, addresses, onCellClick }: AddressGridProps) {
  const list = enumerateNetwork(cidr, GRID_MAX);
  const network = parseCidr(cidr);
  if (list === null || network === null) return null;

  const byAddress = new Map(addresses.map((a) => [a.address, a]));
  const hasNetworkBroadcast = network.version === 4 && network.masklen <= 30;
  const lastIndex = list.length - 1;

  const label = (ip: string) =>
    network.version === 4 ? ip.split(".").pop() : ip.split(":").pop() || ip;

  return (
    <div className="grid grid-cols-[repeat(16,minmax(0,1fr))] gap-1">
      {list.map((ip, index) => {
        const existing = byAddress.get(ip) ?? null;
        const isNetworkOrBroadcast = hasNetworkBroadcast && (index === 0 || index === lastIndex);
        const color = existing
          ? (STATUS_BG[existing.status] ?? "bg-zinc-500 text-white")
          : isNetworkOrBroadcast
            ? "bg-zinc-800/70 text-zinc-600"
            : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700";
        const title = `${ip}${existing ? ` (${existing.status})` : isNetworkOrBroadcast ? " (network/broadcast)" : ""}`;
        return (
          <button
            key={ip}
            type="button"
            title={title}
            onClick={() => onCellClick(ip, existing)}
            className={`rounded px-0.5 py-1 text-center font-mono text-[10px] ${color}`}
          >
            {label(ip)}
          </button>
        );
      })}
    </div>
  );
}
