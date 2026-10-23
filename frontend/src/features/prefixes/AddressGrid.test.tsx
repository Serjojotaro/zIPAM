// SPDX-License-Identifier: Apache-2.0
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { IPAddress } from "../../api/types";
import { AddressGrid } from "./AddressGrid";

function ip(address: string, status: IPAddress["status"]): IPAddress {
  return {
    id: 1,
    vrf: 1,
    address,
    status,
    description: "",
    created_at: "",
    updated_at: "",
  };
}

describe("AddressGrid", () => {
  it("renders every address of a /30 with status titles", () => {
    render(
      <AddressGrid
        cidr="10.0.0.0/30"
        addresses={[ip("10.0.0.1", "active")]}
        onCellClick={() => undefined}
      />,
    );
    const cells = screen.getAllByRole("button");
    expect(cells).toHaveLength(4);
    expect(cells[1]).toHaveAttribute("title", "10.0.0.1 (active)");
    expect(cells[0]).toHaveAttribute("title", "10.0.0.0 (network/broadcast)");
  });

  it("reports free cell clicks with no existing record", () => {
    const onClick = vi.fn();
    render(
      <AddressGrid cidr="10.0.0.0/30" addresses={[ip("10.0.0.1", "active")]} onCellClick={onClick} />,
    );
    fireEvent.click(screen.getByTitle("10.0.0.2"));
    expect(onClick).toHaveBeenCalledWith("10.0.0.2", null);
  });

  it("reports occupied cell clicks with the record", () => {
    const onClick = vi.fn();
    render(
      <AddressGrid cidr="10.0.0.0/30" addresses={[ip("10.0.0.1", "reserved")]} onCellClick={onClick} />,
    );
    fireEvent.click(screen.getByTitle("10.0.0.1 (reserved)"));
    expect(onClick).toHaveBeenCalledWith("10.0.0.1", expect.objectContaining({ status: "reserved" }));
  });
});
