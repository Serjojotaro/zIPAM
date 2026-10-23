// SPDX-License-Identifier: Apache-2.0
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { createColumnHelper } from "@tanstack/react-table";
import { api } from "../../api/client";
import type { Paginated, Prefix, PrefixStatus, Site, Tenant, Vrf } from "../../api/types";
import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../auth/context";
import { buildQuery, errorText, useResource } from "../ipam/hooks";
import { isStrictCidr } from "../ipam/iptools";

const PAGE_SIZE = 50;
const PREFIX_STATUSES: PrefixStatus[] = ["active", "reserved", "container", "deprecated"];

const columnHelper = createColumnHelper<Prefix>();

interface CreateForm {
  vrf: string;
  prefix: string;
  status: PrefixStatus;
  tenant: string;
  site: string;
  description: string;
}

const EMPTY_FORM: CreateForm = {
  vrf: "",
  prefix: "",
  status: "active",
  tenant: "",
  site: "",
  description: "",
};

export function PrefixesPage() {
  const { hasRole } = useAuth();
  const canWrite = hasRole("operator", "admin");

  const [vrfFilter, setVrfFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [textFilter, setTextFilter] = useState("");
  const [appliedText, setAppliedText] = useState("");
  const [page, setPage] = useState(1);

  const [form, setForm] = useState<CreateForm>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const vrfs = useResource<Paginated<Vrf>>("/api/v1/vrfs/?page_size=1024");
  const tenants = useResource<Paginated<Tenant>>("/api/v1/tenants/?page_size=1024");
  const sites = useResource<Paginated<Site>>("/api/v1/sites/?page_size=1024");

  // appliedText is raw user input: the backend returns a stable 400 envelope
  // for invalid IP/CIDR, which useResource surfaces below the table.
  const listPath = `/api/v1/prefixes/${buildQuery({
    vrf: vrfFilter,
    status: statusFilter,
    contains: appliedText,
    page,
    page_size: PAGE_SIZE,
  })}`;
  const prefixes = useResource<Paginated<Prefix>>(listPath);

  const items = prefixes.data?.results ?? [];
  const vrfName = (id: number) => vrfs.data?.results.find((v) => v.id === id)?.name ?? `#${id}`;
  const tenantName = (id: number | null) =>
    id === null ? "—" : tenants.data?.results.find((t) => t.id === id)?.name ?? `#${id}`;
  const siteName = (id: number | null) =>
    id === null ? "—" : sites.data?.results.find((s) => s.id === id)?.name ?? `#${id}`;

  const columns = [
    columnHelper.accessor("prefix", {
      header: "Prefix",
      cell: (info) => (
        <Link to={`/prefixes/${info.row.original.id}`} className="text-emerald-400 hover:underline">
          {info.getValue()}
        </Link>
      ),
    }),
    columnHelper.accessor((row) => vrfName(row.vrf), { id: "vrf", header: "VRF" }),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => <StatusBadge status={info.getValue()} />,
    }),
    columnHelper.accessor((row) => tenantName(row.tenant), { id: "tenant", header: "Tenant" }),
    columnHelper.accessor((row) => siteName(row.site), { id: "site", header: "Site" }),
    columnHelper.accessor("description", {
      header: "Description",
      cell: (info) => <span className="text-zinc-400">{info.getValue() || "—"}</span>,
    }),
  ];

  const applyTextFilter = (event: FormEvent) => {
    event.preventDefault();
    setAppliedText(textFilter.trim());
    setPage(1);
  };

  const createPrefix = (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!isStrictCidr(form.prefix)) {
      setFormError("Prefix must be a strict CIDR (host bits must be zero), e.g. 10.0.0.0/24.");
      return;
    }
    void api
      .post<Prefix>("/api/v1/prefixes/", {
        vrf: Number(form.vrf),
        prefix: form.prefix.trim(),
        status: form.status,
        tenant: form.tenant === "" ? null : Number(form.tenant),
        site: form.site === "" ? null : Number(form.site),
        description: form.description,
      })
      .then(
        () => {
          setForm(EMPTY_FORM);
          prefixes.reload();
        },
        (e: unknown) => setFormError(errorText(e)),
      );
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Prefixes</h2>

      <form onSubmit={applyTextFilter} className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="filter-vrf" className="block text-xs text-zinc-400">
            VRF
          </label>
          <select
            id="filter-vrf"
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
          <label htmlFor="filter-status" className="block text-xs text-zinc-400">
            Status
          </label>
          <select
            id="filter-status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          >
            <option value="">— all —</option>
            {PREFIX_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filter-contains" className="block text-xs text-zinc-400">
            Contains IP (finds covering prefixes)
          </label>
          <input
            id="filter-contains"
            value={textFilter}
            onChange={(e) => setTextFilter(e.target.value)}
            placeholder="10.0.0.5 or 10.0.0.0/24"
            className="mt-1 w-56 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-900"
        >
          Apply
        </button>
        {appliedText !== "" && (
          <button
            type="button"
            onClick={() => {
              setTextFilter("");
              setAppliedText("");
              setPage(1);
            }}
            className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-900"
          >
            Clear
          </button>
        )}
      </form>

      {canWrite && (
        <form onSubmit={createPrefix} className="flex flex-wrap items-end gap-3 rounded border border-zinc-800 p-4">
          <div>
            <label htmlFor="create-vrf" className="block text-xs text-zinc-400">
              VRF
            </label>
            <select
              id="create-vrf"
              required
              value={form.vrf}
              onChange={(e) => setForm({ ...form, vrf: e.target.value })}
              className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              <option value="">— pick —</option>
              {vrfs.data?.results.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="create-prefix" className="block text-xs text-zinc-400">
              Prefix (strict CIDR)
            </label>
            <input
              id="create-prefix"
              required
              value={form.prefix}
              onChange={(e) => setForm({ ...form, prefix: e.target.value })}
              placeholder="10.10.0.0/24"
              className="mt-1 w-44 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label htmlFor="create-status" className="block text-xs text-zinc-400">
              Status
            </label>
            <select
              id="create-status"
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value as PrefixStatus })}
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
            <label htmlFor="create-tenant" className="block text-xs text-zinc-400">
              Tenant
            </label>
            <select
              id="create-tenant"
              value={form.tenant}
              onChange={(e) => setForm({ ...form, tenant: e.target.value })}
              className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              <option value="">— none —</option>
              {tenants.data?.results.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="create-site" className="block text-xs text-zinc-400">
              Site
            </label>
            <select
              id="create-site"
              value={form.site}
              onChange={(e) => setForm({ ...form, site: e.target.value })}
              className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              <option value="">— none —</option>
              {sites.data?.results.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="create-desc" className="block text-xs text-zinc-400">
              Description
            </label>
            <input
              id="create-desc"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="mt-1 w-56 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </div>
          <button type="submit" className="rounded bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500">
            Create
          </button>
        </form>
      )}

      <DataTable
        columns={columns}
        data={items}
        loading={prefixes.loading}
        error={prefixes.error}
        emptyMessage="No prefixes found."
        pagination={{
          page,
          pageSize: PAGE_SIZE,
          count: prefixes.data?.count ?? 0,
          onPageChange: setPage,
        }}
      />
      {formError && <p className="text-sm text-red-400">{formError}</p>}
    </div>
  );
}
