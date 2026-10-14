// SPDX-License-Identifier: Apache-2.0
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

function mockFetch(handler: (url: string) => { status: number; body: unknown }) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      const { status, body } = handler(url);
      return Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        json: async () => body,
      });
    }),
  );
}

beforeEach(() => {
  window.history.pushState({}, "/", "/");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("redirects anonymous users to the login page", async () => {
    mockFetch(() => ({ status: 401, body: { error: { code: "NOT_AUTHENTICATED", message: "" } } }));
    render(<App />);
    expect(await screen.findByText("Sign in to zIPAM", {}, { timeout: 2000 })).toBeInTheDocument();
  });

  it("shows reference data for an authenticated user", async () => {
    mockFetch((url) => {
      if (url.startsWith("/api/v1/auth/me")) {
        return { status: 200, body: { username: "ops", roles: ["operator"] } };
      }
      if (url.includes("/organizations")) {
        return { status: 200, body: { count: 1, next: null, previous: null, results: [{ id: 1, name: "ACME", description: "" }] } };
      }
      return { status: 200, body: { count: 0, next: null, previous: null, results: [] } };
    });
    render(<App />);
    expect(await screen.findByText("ACME", {}, { timeout: 2000 })).toBeInTheDocument();
  });
});
