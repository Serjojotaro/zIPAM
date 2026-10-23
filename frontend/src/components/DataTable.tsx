// SPDX-License-Identifier: Apache-2.0
// The single table wrapper for the app (ADR-0007): TanStack Table headless
// state (selection, structure) + optional windowed rendering for big lists
// (§62). Data itself is always server-paginated (§14) — manualPagination.
import { useRef } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type Row,
  type RowSelectionState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";

export interface TablePagination {
  page: number;
  pageSize: number;
  count: number;
  onPageChange: (page: number) => void;
}

interface DataTableProps<T extends { id: number }> {
  // TanStack's canonical column-array type; the one documented `any`
  // exception of §31 — heterogeneous TValue columns do not unify otherwise.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: ColumnDef<T, any>[];
  data: T[];
  loading: boolean;
  error: string | null;
  emptyMessage?: string;
  virtualize?: boolean;
  pagination?: TablePagination;
  selectable?: boolean;
  selectedIds?: number[];
  onSelectionChange?: (ids: number[]) => void;
}

function toSelectionState(ids: number[] | undefined): RowSelectionState {
  return Object.fromEntries((ids ?? []).map((id) => [String(id), true]));
}

function fromSelectionState(state: RowSelectionState): number[] {
  return Object.entries(state)
    .filter(([, selected]) => selected)
    .map(([id]) => Number(id));
}

export function DataTable<T extends { id: number }>({
  columns,
  data,
  loading,
  error,
  emptyMessage = "No records.",
  virtualize = false,
  pagination,
  selectable = false,
  selectedIds,
  onSelectionChange,
}: DataTableProps<T>) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const selectColumn: ColumnDef<T> = {
    id: "select",
    size: 32,
    header: ({ table }) => (
      <input
        type="checkbox"
        aria-label="Select all rows on page"
        checked={table.getIsAllRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
        className="accent-emerald-600"
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        aria-label="Select row"
        checked={row.getIsSelected()}
        onChange={row.getToggleSelectedHandler()}
        className="accent-emerald-600"
      />
    ),
  };

  const table = useReactTable<T>({
    data,
    columns: selectable ? [selectColumn, ...columns] : columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    enableRowSelection: selectable,
    getRowId: (row) => String(row.id),
    state: { rowSelection: toSelectionState(selectedIds) },
    onRowSelectionChange: (updater) => {
      if (!onSelectionChange) return;
      const next = typeof updater === "function" ? updater(toSelectionState(selectedIds)) : updater;
      onSelectionChange(fromSelectionState(next));
    },
  });

  const rows = table.getRowModel().rows;
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 40,
    overscan: 12,
    enabled: virtualize,
  });

  const renderRow = (row: Row<T>) => (
    <tr
      key={row.id}
      className="h-10 border-b border-zinc-900 hover:bg-zinc-900/40"
    >
      {row.getVisibleCells().map((cell) => (
        <td key={cell.id} className="truncate px-3 py-2 align-top">
          {flexRender(cell.column.columnDef.cell, cell.getContext())}
        </td>
      ))}
    </tr>
  );

  const leafColumnCount = table.getVisibleLeafColumns().length;
  const virtualItems = virtualizer.getVirtualItems();
  const spacerCell = (height: number) => (
    <td aria-hidden colSpan={leafColumnCount} style={{ height, padding: 0, border: 0 }} />
  );

  const pageCount = pagination ? Math.max(1, Math.ceil(pagination.count / pagination.pageSize)) : 1;

  return (
    <div className="space-y-2">
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div ref={scrollRef} className={virtualize ? "max-h-[70vh] overflow-auto" : undefined}>
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950 text-xs uppercase text-zinc-500">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-3 py-2 font-medium">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={leafColumnCount} className="px-3 py-4 text-zinc-500">
                  Loading…
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={leafColumnCount} className="px-3 py-4 text-zinc-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : virtualize ? (
              <>
                <tr>{spacerCell(virtualItems[0]?.start ?? 0)}</tr>
                {virtualItems.map((item) => renderRow(rows[item.index]))}
                <tr>
                  {spacerCell(
                    Math.max(0, virtualizer.getTotalSize() - (virtualItems.at(-1)?.end ?? 0)),
                  )}
                </tr>
              </>
            ) : (
              rows.map(renderRow)
            )}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="flex items-center gap-3 text-sm text-zinc-400">
          <span>
            {pagination.count} records · page {pagination.page} of {pageCount}
          </span>
          <button
            type="button"
            disabled={pagination.page <= 1}
            onClick={() => pagination.onPageChange(pagination.page - 1)}
            className="rounded border border-zinc-700 px-2 py-1 disabled:opacity-40"
          >
            Prev
          </button>
          <button
            type="button"
            disabled={pagination.page >= pageCount}
            onClick={() => pagination.onPageChange(pagination.page + 1)}
            className="rounded border border-zinc-700 px-2 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
