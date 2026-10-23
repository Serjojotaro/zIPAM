// SPDX-License-Identifier: Apache-2.0
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { UtilizationBar } from "./UtilizationBar";

describe("UtilizationBar", () => {
  it("renders allocated/total and percent", () => {
    render(
      <UtilizationBar util={{ total: 254, allocated: 1, available: 253, utilization_percent: 0.39 }} />,
    );
    expect(screen.getByText("1 / 254 allocated · 253 available")).toBeInTheDocument();
    expect(screen.getByText("0.39%")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0.39");
  });

  it("clamps a percent above 100", () => {
    render(
      <UtilizationBar util={{ total: 2, allocated: 3, available: 0, utilization_percent: 150 }} />,
    );
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
  });

  it("renders nothing without data", () => {
    const { container } = render(<UtilizationBar util={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
