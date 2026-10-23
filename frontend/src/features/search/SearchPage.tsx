// SPDX-License-Identifier: Apache-2.0
import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import type { SearchResponse, SearchResultGroup } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";
import { buildQuery, useResource } from "../ipam/hooks";

function Group({
  title,
  items,
  render,
}: {
  title: string;
  items: SearchResultGroup[];
  render: (item: SearchResultGroup) => ReactNode;
}) {
  if (items.length === 0) return null;
  return (
    <section className="space-y-1">
      <h3 className="text-xs font-semibold uppercase text-zinc-500">
        {title} ({items.length})
      </h3>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.id} className="text-sm">
            {render(item)}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function SearchPage() {
  const [q, setQ] = useState("");
  const [applied, setApplied] = useState("");

  const search = useResource<SearchResponse>(
    applied.trim().length >= 2 ? `/api/v1/search${buildQuery({ q: applied.trim() })}` : null,
  );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setApplied(q);
  };

  const results = search.data?.results;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Search</h2>
      <form onSubmit={submit} className="flex gap-2">
        <input
          aria-label="Search query"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="IP address, CIDR, name or VLAN id…"
          className="w-96 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm"
        />
        <button type="submit" className="rounded bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500">
          Search
        </button>
      </form>

      {search.loading && <p className="text-sm text-zinc-400">Searching…</p>}
      {search.error && <p className="text-sm text-red-400">{search.error}</p>}

      {results && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <Group
            title="Prefixes"
            items={results.prefixes}
            render={(r) => (
              <Link to={`/prefixes/${r.id}`} className="text-emerald-400 hover:underline">
                <span className="font-mono">{r.prefix}</span>{" "}
                {r.status && <StatusBadge status={r.status} />}
              </Link>
            )}
          />
          <Group
            title="IP addresses"
            items={results.ip_addresses}
            render={(r) => (
              <Link
                to={`/ip-addresses?address=${encodeURIComponent(r.address ?? "")}`}
                className="text-emerald-400 hover:underline"
              >
                <span className="font-mono">{r.address}</span>{" "}
                {r.status && <StatusBadge status={r.status} />}
              </Link>
            )}
          />
          <Group
            title="VLANs"
            items={results.vlans}
            render={(r) => (
              <span>
                {r.name} <span className="text-zinc-500">vid {r.vid}</span>
              </span>
            )}
          />
          <Group title="VRFs" items={results.vrfs} render={(r) => <span>{r.name}</span>} />
          <Group
            title="Organizations"
            items={results.organizations}
            render={(r) => (
              <Link to="/organizations" className="hover:underline">
                {r.name}
              </Link>
            )}
          />
          <Group
            title="Tenants"
            items={results.tenants}
            render={(r) => (
              <Link to="/tenants" className="hover:underline">
                {r.name}
              </Link>
            )}
          />
          <Group
            title="Regions"
            items={results.regions}
            render={(r) => (
              <Link to="/regions" className="hover:underline">
                {r.name}
              </Link>
            )}
          />
          <Group
            title="Sites"
            items={results.sites}
            render={(r) => (
              <Link to="/sites" className="hover:underline">
                {r.name}
              </Link>
            )}
          />
          {results &&
            Object.values(results).every((group) => group.length === 0) && (
              <p className="text-sm text-zinc-500">Nothing found for “{search.data?.query}”.</p>
            )}
        </div>
      )}
    </div>
  );
}
