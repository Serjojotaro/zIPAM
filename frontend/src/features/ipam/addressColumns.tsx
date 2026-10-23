// SPDX-License-Identifier: Apache-2.0
import { createColumnHelper } from "@tanstack/react-table";
import type { IPAddress } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";

const helper = createColumnHelper<IPAddress>();

export interface AddressRowHandlers {
  canWrite: boolean;
  onEdit: (ip: IPAddress) => void;
  onRelease: (ip: IPAddress) => void;
}

export function addressColumns(handlers: AddressRowHandlers, vrfName?: (id: number) => string) {
  return [
    helper.accessor("address", { header: "Address" }),
    ...(vrfName
      ? [helper.accessor("vrf", { id: "vrf", header: "VRF", cell: (info) => vrfName(info.getValue()) })]
      : []),
    helper.accessor("status", {
      header: "Status",
      cell: (info) => <StatusBadge status={info.getValue()} />,
    }),
    helper.accessor("description", {
      header: "Description",
      cell: (info) => <span className="text-zinc-400">{info.getValue() || "—"}</span>,
    }),
    helper.accessor("updated_at", {
      id: "updated",
      header: "Updated",
      cell: (info) => new Date(info.getValue()).toLocaleString(),
    }),
    helper.display({
      id: "actions",
      header: "",
      cell: ({ row }) =>
        handlers.canWrite ? (
          <span className="space-x-2 whitespace-nowrap">
            <button
              type="button"
              onClick={() => handlers.onEdit(row.original)}
              className="text-emerald-400 hover:underline"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => handlers.onRelease(row.original)}
              className="text-red-400 hover:underline"
            >
              Release
            </button>
          </span>
        ) : null,
    }),
  ];
}
