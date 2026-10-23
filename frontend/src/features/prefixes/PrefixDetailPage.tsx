// SPDX-License-Identifier: Apache-2.0
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createColumnHelper } from "@tanstack/react-table";
import { api } from "../../api/client";
import type {
  AvailableSubnetsResponse,
  IPAddress,
  IpStatus,
  Paginated,
  Prefix,
  PrefixStatus,
  Utilization,
} from "../../api/types";
import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../auth/context";
import { addressColumns } from "../ipam/addressColumns";
import { buildQuery, errorText, useResource } from "../ipam/hooks";
import { UtilizationBar } from "../ipam/UtilizationBar";
import { AddressGrid, GRID_MAX } from "./AddressGrid";

const ADDRESS_PAGE_SIZE = 50;
const PREFIX_STATUSES: PrefixStatus[] = ["active", "reserved", "container", "deprecated"];
const IP_STATUSES: IpStatus[] = ["active", "reserved", "deprecated"];

const childHelper = createColumnHelper<Prefix>();

type Editor = { mode: "edit"; ip: IPAddress } | { mode: "assign"; address: string } | null;

export function PrefixDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const canWrite = hasRole("operator", "admin");

  const prefix = useResource<Prefix>(`/api/v1/prefixes/${id}/`);
  const util = useResource<Utilization>(`/api/v1/prefixes/${id}/utilization/`);
  const children = useResource<Paginated<Prefix>>(
    `/api/v1/prefixes/${buildQuery({ parent: id, page_size: 1024 })}`,
  );
  const ancestors = useResource<Paginated<Prefix>>(
    prefix.data
      ? `/api/v1/prefixes/${buildQuery({ contains: prefix.data.prefix, vrf: prefix.data.vrf, page_size: 1024 })}`
      : null,
  );
  const grid = useResource<Paginated<IPAddress>>(
    prefix.data && util.data && util.data.total <= GRID_MAX
      ? `/api/v1/ip-addresses/${buildQuery({ within: prefix.data.prefix, page_size: GRID_MAX })}`
      : null,
  );
  const [addressPage, setAddressPage] = useState(1);
  const addresses = useResource<Paginated<IPAddress>>(
    prefix.data
      ? `/api/v1/ip-addresses/${buildQuery({
          within: prefix.data.prefix,
          page: addressPage,
          page_size: ADDRESS_PAGE_SIZE,
        })}`
      : null,
  );

  const [actionError, setActionError] = useState<string | null>(null);
  const [allocStatus, setAllocStatus] = useState<IpStatus>("active");
  const [allocDesc, setAllocDesc] = useState("");
  const [splitLen, setSplitLen] = useState("");
  const [masklen, setMasklen] = useState("");
  const [freeSubnets, setFreeSubnets] = useState<string[] | null>(null);
  const [editor, setEditor] = useState<Editor>(null);
  const [editorStatus, setEditorStatus] = useState<IpStatus>("active");
  const [editorDesc, setEditorDesc] = useState("");
  const [pStatus, setPStatus] = useState<PrefixStatus>("active");
  const [pDesc, setPDesc] = useState("");

  useEffect(() => {
    if (prefix.data) {
      setPStatus(prefix.data.status);
      setPDesc(prefix.data.description);
    }
  }, [prefix.data]);

  const reloadAll = () => {
    prefix.reload();
    util.reload();
    children.reload();
    addresses.reload();
    grid.reload();
    void loadFreeSubnets();
  };

  const loadFreeSubnets = () =>
    api
      .post<AvailableSubnetsResponse>(
        `/api/v1/prefixes/${id}/available-subnets/`,
        masklen.trim() === "" ? {} : { masklen: Number(masklen) },
      )
      .then(
        (r) => setFreeSubnets(r.available_subnets),
        (e: unknown) => setActionError(errorText(e)),
      );

  useEffect(() => {
    if (prefix.data) void loadFreeSubnets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefix.data]);

  const run = (promise: Promise<unknown>, onOk?: () => void) => {
    setActionError(null);
    promise.then(
      () => (onOk ? onOk() : reloadAll()),
      (e: unknown) => setActionError(errorText(e)),
    );
  };

  const allocate = () =>
    run(
      api.post(`/api/v1/prefixes/${id}/allocate/`, { status: allocStatus, description: allocDesc }),
    );

  const split = () => {
    const len = Number(splitLen);
    if (!Number.isInteger(len)) {
      setActionError("prefix_len must be an integer.");
      return;
    }
    run(api.post(`/api/v1/prefixes/${id}/split/`, { prefix_len: len }), () => {
      setSplitLen("");
      reloadAll();
    });
  };

  const releaseIp = (ip: IPAddress) => {
    if (!window.confirm(`Release ${ip.address}?`)) return;
    run(api.delete(`/api/v1/ip-addresses/${ip.id}/`));
  };

  const openEditor = (mode: Editor) => {
    setEditor(mode);
    setActionError(null);
    if (mode !== null && mode.mode === "edit") {
      setEditorStatus(mode.ip.status);
      setEditorDesc(mode.ip.description);
    } else {
      setEditorStatus("active");
      setEditorDesc("");
    }
  };

  const saveEditor = () => {
    if (editor === null) return;
    if (editor.mode === "edit") {
      run(
        api.patch(`/api/v1/ip-addresses/${editor.ip.id}/`, {
          status: editorStatus,
          description: editorDesc,
        }),
        () => {
          setEditor(null);
          reloadAll();
        },
      );
    } else {
      if (prefix.data === null) return;
      run(
        api.post("/api/v1/ip-addresses/", {
          vrf: prefix.data.vrf,
          address: editor.address,
          status: editorStatus,
          description: editorDesc,
        }),
        () => {
          setEditor(null);
          reloadAll();
        },
      );
    }
  };

  const savePrefix = (event: FormEvent) => {
    event.preventDefault();
    run(api.patch(`/api/v1/prefixes/${id}/`, { status: pStatus, description: pDesc }));
  };

  const deletePrefix = () => {
    if (prefix.data === null) return;
    if (!window.confirm(`Delete prefix ${prefix.data.prefix}? Addresses/children must be removed first.`)) return;
    run(api.delete(`/api/v1/prefixes/${id}/`), () => navigate("/prefixes"));
  };

  if (prefix.loading && prefix.data === null) return <p className="text-zinc-400">Loading…</p>;
  if (prefix.error) return <p className="text-sm text-red-400">{prefix.error}</p>;
  const data = prefix.data;
  if (data === null) return null;

  const breadcrumb = (ancestors.data?.results ?? [])
    .filter((p) => p.id !== data.id)
    .sort((a, b) => Number(a.prefix.split("/")[1]) - Number(b.prefix.split("/")[1]));

  const columns = addressColumns({
    canWrite,
    onEdit: (ip) => openEditor({ mode: "edit", ip }),
    onRelease: releaseIp,
  });

  const childColumns = [
    childHelper.accessor("prefix", {
      header: "Child prefix",
      cell: (info) => (
        <Link to={`/prefixes/${info.row.original.id}`} className="text-emerald-400 hover:underline">
          {info.getValue()}
        </Link>
      ),
    }),
    childHelper.accessor("status", {
      header: "Status",
      cell: (info) => <StatusBadge status={info.getValue()} />,
    }),
    childHelper.accessor("description", {
      header: "Description",
      cell: (info) => <span className="text-zinc-400">{info.getValue() || "—"}</span>,
    }),
  ];

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <div className="min-w-0 flex-1 space-y-6">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-xs text-zinc-500">
          {breadcrumb.map((a) => (
            <span key={a.id} className="flex items-center gap-1">
              <Link to={`/prefixes/${a.id}`} className="hover:text-zinc-300 hover:underline">
                {a.prefix}
              </Link>
              <span aria-hidden>/</span>
            </span>
          ))}
          <span className="text-zinc-300">{data.prefix}</span>
        </nav>

        <header className="flex flex-wrap items-center gap-3">
          <h2 className="font-mono text-xl font-semibold">{data.prefix}</h2>
          <StatusBadge status={data.status} />
          <span className="text-sm text-zinc-500">VRF #{data.vrf}</span>
          {canWrite && (
            <button
              type="button"
              onClick={deletePrefix}
              className="ml-auto rounded border border-red-900 px-3 py-1 text-sm text-red-400 hover:bg-red-950"
            >
              Delete prefix
            </button>
          )}
        </header>

        <section className="rounded border border-zinc-800 p-4">
          <h3 className="mb-3 text-sm font-semibold text-zinc-300">Utilization</h3>
          <UtilizationBar util={util.data} />
        </section>

        {canWrite && (
          <form onSubmit={savePrefix} className="flex flex-wrap items-end gap-3 rounded border border-zinc-800 p-4">
            <div>
              <label htmlFor="p-status" className="block text-xs text-zinc-400">
                Prefix status
              </label>
              <select
                id="p-status"
                value={pStatus}
                onChange={(e) => setPStatus(e.target.value as PrefixStatus)}
                className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              >
                {PREFIX_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="p-desc" className="block text-xs text-zinc-400">
                Description
              </label>
              <input
                id="p-desc"
                value={pDesc}
                onChange={(e) => setPDesc(e.target.value)}
                className="mt-1 w-72 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              />
            </div>
            <button type="submit" className="rounded bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500">
              Save
            </button>
          </form>
        )}

        {grid.data !== null && (
          <section className="space-y-2 rounded border border-zinc-800 p-4">
            <h3 className="text-sm font-semibold text-zinc-300">Address grid</h3>
            <p className="text-xs text-zinc-500">
              Click a cell to allocate (free) or edit/release (occupied).
            </p>
            <AddressGrid
              cidr={data.prefix}
              addresses={grid.data.results}
              onCellClick={(address, existing) =>
                openEditor(existing ? { mode: "edit", ip: existing } : { mode: "assign", address })
              }
            />
          </section>
        )}

        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-zinc-300">Addresses in {data.prefix}</h3>
          <DataTable
            columns={columns}
            data={addresses.data?.results ?? []}
            loading={addresses.loading}
            error={addresses.error}
            emptyMessage="No addresses allocated."
            virtualize
            pagination={{
              page: addressPage,
              pageSize: ADDRESS_PAGE_SIZE,
              count: addresses.data?.count ?? 0,
              onPageChange: setAddressPage,
            }}
          />
        </section>
      </div>

      <aside className="w-full shrink-0 space-y-6 lg:w-80">
        {canWrite && (
          <section className="space-y-2 rounded border border-zinc-800 p-4">
            <h3 className="text-sm font-semibold text-zinc-300">Allocate address</h3>
            <div className="flex gap-2">
              <select
                aria-label="Allocate status"
                value={allocStatus}
                onChange={(e) => setAllocStatus(e.target.value as IpStatus)}
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              >
                {IP_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={allocate}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
              >
                Allocate
              </button>
            </div>
            <input
              aria-label="Allocate description"
              value={allocDesc}
              onChange={(e) => setAllocDesc(e.target.value)}
              placeholder="Description (optional)"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </section>
        )}

        {canWrite && (
          <section className="space-y-2 rounded border border-zinc-800 p-4">
            <h3 className="text-sm font-semibold text-zinc-300">Split prefix</h3>
            <div className="flex gap-2">
              <input
                aria-label="Split prefix length"
                value={splitLen}
                onChange={(e) => setSplitLen(e.target.value)}
                placeholder="/26"
                className="w-20 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              />
              <button
                type="button"
                onClick={split}
                className="rounded border border-zinc-700 px-3 py-1 text-sm hover:bg-zinc-900"
              >
                Split
              </button>
            </div>
            <p className="text-xs text-zinc-500">
              Allowed only while the prefix has no children and no allocated addresses.
            </p>
          </section>
        )}

        <section className="space-y-2 rounded border border-zinc-800 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-300">Free subnets</h3>
            <div className="flex gap-1">
              <input
                aria-label="Free subnet masklen"
                value={masklen}
                onChange={(e) => setMasklen(e.target.value)}
                placeholder="masklen"
                className="w-20 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              />
              <button
                type="button"
                onClick={() => void loadFreeSubnets()}
                className="rounded border border-zinc-700 px-2 py-1 text-sm hover:bg-zinc-900"
              >
                Recalc
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {freeSubnets === null ? (
              <span className="text-xs text-zinc-500">—</span>
            ) : freeSubnets.length === 0 ? (
              <span className="text-xs text-zinc-500">no free space</span>
            ) : (
              freeSubnets.map((s) => (
                <span key={s} className="rounded bg-sky-500/15 px-1.5 py-0.5 font-mono text-xs text-sky-400">
                  {s}
                </span>
              ))
            )}
          </div>
        </section>

        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-zinc-300">Child prefixes</h3>
          <DataTable
            columns={childColumns}
            data={children.data?.results ?? []}
            loading={children.loading}
            error={children.error}
            emptyMessage="No child prefixes."
          />
        </section>

        {editor !== null && (
          <section className="space-y-2 rounded border border-emerald-900 p-4">
            <h3 className="text-sm font-semibold">
              {editor.mode === "edit" ? `Edit ${editor.ip.address}` : `Allocate ${editor.address}`}
            </h3>
            <select
              aria-label="Editor status"
              value={editorStatus}
              onChange={(e) => setEditorStatus(e.target.value as IpStatus)}
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              {IP_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <input
              aria-label="Editor description"
              value={editorDesc}
              onChange={(e) => setEditorDesc(e.target.value)}
              placeholder="Description"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={saveEditor}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
              >
                Save
              </button>
              {editor.mode === "edit" && (
                <button
                  type="button"
                  onClick={() => releaseIp(editor.ip)}
                  className="rounded border border-red-900 px-3 py-1 text-sm text-red-400 hover:bg-red-950"
                >
                  Release
                </button>
              )}
              <button
                type="button"
                onClick={() => setEditor(null)}
                className="rounded border border-zinc-700 px-3 py-1 text-sm text-zinc-300"
              >
                Close
              </button>
            </div>
          </section>
        )}

        {actionError && <p className="text-sm text-red-400">{actionError}</p>}
      </aside>
    </div>
  );
}
