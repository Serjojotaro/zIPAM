// SPDX-License-Identifier: Apache-2.0
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(status: "ok" | "fail"): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status === "ok",
      json: async () => ({ status: "ok" }),
    }),
  );
}

describe("App", () => {
  it("shows backend OK after successful health check", async () => {
    stubFetch("ok");
    render(<App />);
    expect(await screen.findByText("Backend: OK", {}, { timeout: 2000 })).toBeInTheDocument();
  });

  it("shows unreachable when health check fails", async () => {
    stubFetch("fail");
    render(<App />);
    expect(await screen.findByText("Backend: unreachable", {}, { timeout: 2000 })).toBeInTheDocument();
  });
});
