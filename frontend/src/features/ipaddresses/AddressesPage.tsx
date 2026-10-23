// SPDX-License-Identifier: Apache-2.0
import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import type { IPAddress, IpStatus, Paginated, Vrf } from "../../api/types";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../auth/context";
import { addressColumns } from "../ipam/addressColumns";
import { buildQuery, errorText, useResource } from "../ipam/hooks";

const PAGE_SIZE = 50;
const IP_STATUSES: IpStatus[] = ["active", "reserved", "deprecated"];

export function AddressesPage() {
  const { hasRole } = useAuth();
  const canWrite = hasRole("operator", "admin");
  const [searchParams] = useSearchParams();

  const [vrfFilter, setVrfFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [addressFilter, setAddressFilter] = useState(searchParams.get("address") ?? "");
  const [withinFilter, setWithinFilter] = useState("");
  const [appliedWithin, setAppliedWithin] = useState("");
  const [page, setPage] = useState(1);

  const [selected, setSelected] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [bulkMsg, setBulkMsg] = useState<string | null>(null);
  const [editing, setEditing] = useState<IPAddress | null>(null);
  const [editStatus, setEditStatus] = useState<IpStatus>("active");
  const [editDesc, setEditDesc] = useState("");

  const vrfs = useResource<Paginated<Vrf>>("/api/v1/vrfs/?page_size=1024");
  const listPath = `/api/v1/ip-addresses/${buildQuery({
    vrf: vrfFilter,
    status: statusFilter,
    address: addressFilter.trim(),
    within: appliedWithin,
    page,
    page_size: PAGE_SIZE,
  })}`;
  const addresses = useResource<Paginated<IPAddress>>(listPath);
  const vrfName = (id: number) => vrfs.data?.results.find((v) => v.id === id)?.name ?? `#${id}`;

  const releaseOne = (ip: IPAddress) => {
    if (!window.confirm(`Release ${ip.address}?`)) return;
    void api.delete(`/api/v1/ip-addresses/${ip.id}/`).then(
      () => addresses.reload(),
      (e: unknown) => setBulkMsg(errorText(e)),
    );
  };

  const columns = addressColumns(
    {
      canWrite,
      onEdit: (ip) => {
        setEditing(ip);
        setEditStatus(ip.status);
        setEditDesc(ip.description);
      },
      onRelease: releaseOne,
    },
    vrfName,
  );

  // Minimal bulk release (§24): sequential, partial failures reported.
  const releaseSelected = async () => {
    if (selected.length === 0) return;
    if (!window.confirm(`Release ${selected.length} selected address(es)?`)) return;
    setBusy(true);
    setBulkMsg(null);
    let released = 0;
    const failed: string[] = [];
    for (const id of selected) {
      try {
        await api.delete(`/api/v1/ip-addresses/${id}/`);
        released += 1;
      } catch (e: unknown) {
        failed.push(`#${id}: ${errorText(e)}`);
      }
    }
    setSelected([]);
    setBusy(false);
    setBulkMsg(
      failed.length === 0
        ? `Released ${released}.`
        : `Released ${released}, failed ${failed.length}: ${failed.slice(0, 3).join("; ")}`,
    );
    addresses.reload();
  };

  const saveEdit = (event: FormEvent) => {
    event.preventDefault();
    if (editing === null) return;
    void api
      .patch(`/api/v1/ip-addresses/${editing.id}/`, { status: editStatus, description: editDesc })
      .then(
        () => {
          setEditing(null);
          addresses.reload();
        },
        (e: unknown) => setBulkMsg(errorText(e)),
      );
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">IP Addresses</h2>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setAppliedWithin(withinFilter.trim());
          setPage(1);
        }}
        className="flex flex-wrap items-end gap-3"
      >
        <div>
          <label htmlFor="addr-vrf" className="block text-xs text-zinc-400">
            VRF
          </label>
          <select
            id="addr-vrf"
            value={vrfFilter}
            onChange={(e) => {
              setVrfFilter(e.target.value);
              setPage(1);
            }}
            className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          >
            <option value="">— all —</option>
            {vrfs.data?.results.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="addr-status" className="block text-xs text-zinc-400">
            Status
          </label>
          <select
            id="addr-status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          >
            <option value="">— all —</option>
            {IP_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="addr-address" className="block text-xs text-zinc-400">
            Address (exact)
          </label>
          <input
            id="addr-address"
            value={addressFilter}
            onChange={(e) => {
              setAddressFilter(e.target.value);
              setPage(1);
            }}
            placeholder="10.0.0.5"
            className="mt-1 w-40 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label htmlFor="addr-within" className="block text-xs text-zinc-400">
            Within CIDR
          </label>
          <input
            id="addr-within"
            value={withinFilter}
            onChange={(e) => setWithinFilter(e.target.value)}
            placeholder="10.0.0.0/24"
            className="mt-1 w-44 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-900"
        >
          Apply
        </button>
      </form>

      {canWrite && (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            disabled={selected.length === 0 || busy}
            onClick={() => void releaseSelected()}
            className="rounded border border-red-900 px-3 py-1.5 text-sm text-red-400 hover:bg-red-950 disabled:opacity-40"
          >
            Release selected ({selected.length})
          </button>
          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => setSelected([])}
              className="text-sm text-zinc-400 hover:underline"
            >
              Clear selection
            </button>
          )}
        </div>
      )}

      {editing && (
        <form onSubmit={saveEdit} className="flex flex-wrap items-end gap-3 rounded border border-emerald-900 p-4">
          <div className="text-sm font-medium">{editing.address}</div>
          <div>
            <label htmlFor="edit-status" className="block text-xs text-zinc-400">
              Status
            </label>
            <select
              id="edit-status"
              value={editStatus}
              onChange={(e) => setEditStatus(e.target.value as IpStatus)}
              className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              {IP_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="edit-desc" className="block text-xs text-zinc-400">
              Description
            </label>
            <input
              id="edit-desc"
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              className="mt-1 w-64 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </div>
          <button type="submit" className="rounded bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500">
            Save
          </button>
          <button
            type="button"
            onClick={() => setEditing(null)}
            className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300"
          >
            Close
          </button>
        </form>
      )}

      {bulkMsg && <p className="text-sm text-zinc-400">{bulkMsg}</p>}

      <DataTable
        columns={columns}
        data={addresses.data?.results ?? []}
        loading={addresses.loading}
        error={addresses.error}
        emptyMessage="No addresses found."
        virtualize
        selectable={canWrite}
        selectedIds={selected}
        onSelectionChange={setSelected}
        pagination={{
          page,
          pageSize: PAGE_SIZE,
          count: addresses.data?.count ?? 0,
          onPageChange: setPage,
        }}
      />
      <p className="text-xs text-zinc-600">
        VRF shown by lookup over first 1024 VRFs (draft limit).
      </p>
    </div>
  );
}
