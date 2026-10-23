// SPDX-License-Identifier: Apache-2.0
import { render, screen } from "@testing-library/react";
import { createColumnHelper } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";
import { DataTable } from "./DataTable";

interface Row {
  id: number;
  name: string;
}

const helper = createColumnHelper<Row>();
const columns = [helper.accessor("name", { header: "Name" })];

function manyRows(count: number): Row[] {
  return Array.from({ length: count }, (_, i) => ({ id: i + 1, name: `row-${i}` }));
}

describe("DataTable", () => {
  it("shows the empty state", () => {
    render(<DataTable columns={columns} data={[]} loading={false} error={null} emptyMessage="Nope." />);
    expect(screen.getByText("Nope.")).toBeInTheDocument();
  });

  it("renders server-paginated page rows", () => {
    render(
      <DataTable
        columns={columns}
        data={manyRows(10)}
        loading={false}
        error={null}
        pagination={{ page: 2, pageSize: 10, count: 45, onPageChange: () => undefined }}
      />,
    );
    expect(screen.getByText("row-0")).toBeInTheDocument();
    expect(screen.getByText("45 records · page 2 of 5")).toBeInTheDocument();
  });

  it("window-renders big lists when virtualized (M4 DoD: >10k rows)", () => {
    const { container } = render(
      <DataTable columns={columns} data={manyRows(10000)} loading={false} error={null} virtualize />,
    );
    const bodyRows = container.querySelectorAll("tbody tr").length;
    expect(bodyRows).toBeGreaterThan(0);
    expect(bodyRows).toBeLessThan(200);
  });
});
