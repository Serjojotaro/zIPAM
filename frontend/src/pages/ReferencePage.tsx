// SPDX-License-Identifier: Apache-2.0
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import type { Paginated, ReferenceRecord } from "../api/types";
import { useAuth } from "../auth/context";

interface ForeignKeyOption {
  value: number | null;
  label: string;
}

interface ReferencePageConfig {
  endpoint: string;
  title: string;
  foreignKey?: {
    field: string;
    label: string;
    optionsEndpoint: string;
  };
}

interface FormState {
  name: string;
  description: string;
  foreignKey: string;
}

const EMPTY_FORM: FormState = { name: "", description: "", foreignKey: "" };

export function ReferencePage({ config }: { config: ReferencePageConfig }) {
  const { hasRole } = useAuth();
  const canWrite = hasRole("operator", "admin");

  const [items, setItems] = useState<ReferenceRecord[]>([]);
  const [options, setOptions] = useState<ForeignKeyOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  const load = useCallback(() => {
    api
      .get<Paginated<ReferenceRecord>>(`/api/v1/${config.endpoint}/`)
      .then((page) => setItems(page.results))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load"));
    if (config.foreignKey) {
      api
        .get<Paginated<{ id: number; name: string }>>(`/api/v1/${config.foreignKey.optionsEndpoint}/`)
        .then((page) =>
          setOptions([
            { value: null, label: "— none —" },
            ...page.results.map((r) => ({ value: r.id, label: r.name })),
          ]),
        );
    }
  }, [config]);

  useEffect(load, [load]);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const startEdit = (item: ReferenceRecord) => {
    setEditingId(item.id);
    const fkField = config.foreignKey?.field;
    const fkValue = fkField === undefined ? "" : String((item as unknown as Record<string, unknown>)[fkField] ?? "");
    setForm({ name: item.name, description: item.description, foreignKey: fkValue });
  };

  const payload = (): Record<string, unknown> => {
    const data: Record<string, unknown> = { name: form.name, description: form.description };
    if (config.foreignKey) {
      data[config.foreignKey.field] = form.foreignKey === "" ? null : Number(form.foreignKey);
    }
    return data;
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const done = () => {
      resetForm();
      load();
    };
    const failed = (e: unknown) =>
      setError(e instanceof ApiError ? `${e.code}: ${e.message}` : "Save failed");
    if (editingId === null) {
      void api.post(`/api/v1/${config.endpoint}/`, payload()).then(done, failed);
    } else {
      void api.patch(`/api/v1/${config.endpoint}/${editingId}/`, payload()).then(done, failed);
    }
  };

  const remove = (id: number) => {
    if (!window.confirm("Delete this record?")) return;
    void api.delete(`/api/v1/${config.endpoint}/${id}/`).then(load, (e: unknown) =>
      setError(e instanceof ApiError ? `${e.code}: ${e.message}` : "Delete failed"),
    );
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">{config.title}</h2>

      {canWrite && (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded border border-zinc-800 p-4">
          <div>
            <label htmlFor="ref-name" className="block text-xs text-zinc-400">
              Name
            </label>
            <input
              id="ref-name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="mt-1 w-48 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label htmlFor="ref-desc" className="block text-xs text-zinc-400">
              Description
            </label>
            <input
              id="ref-desc"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="mt-1 w-64 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            />
          </div>
          {config.foreignKey && (
            <div>
              <label htmlFor="ref-fk" className="block text-xs text-zinc-400">
                {config.foreignKey.label}
              </label>
              <select
                id="ref-fk"
                value={form.foreignKey}
                onChange={(e) => setForm({ ...form, foreignKey: e.target.value })}
                className="mt-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
              >
                {options.map((opt) => (
                  <option key={opt.label} value={opt.value === null ? "" : String(opt.value)}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}
          <button
            type="submit"
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500"
          >
            {editingId === null ? "Create" : "Update"}
          </button>
          {editingId !== null && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300"
            >
              Cancel
            </button>
          )}
        </form>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-800 text-xs uppercase text-zinc-500">
          <tr>
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Description</th>
            <th className="py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b border-zinc-900">
              <td className="py-2 pr-4">{item.name}</td>
              <td className="py-2 pr-4 text-zinc-400">{item.description}</td>
              <td className="py-2 text-right">
                {canWrite && (
                  <>
                    <button
                      type="button"
                      onClick={() => startEdit(item)}
                      className="mr-2 text-emerald-400 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(item.id)}
                      className="text-red-400 hover:underline"
                    >
                      Delete
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={3} className="py-4 text-zinc-500">
                No records.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
