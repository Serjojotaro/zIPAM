// SPDX-License-Identifier: Apache-2.0
import type { ApiErrorBody, CurrentUser } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let csrfToken: string | null = null;

async function ensureCsrf(): Promise<string> {
  if (csrfToken !== null) return csrfToken;
  const response = await fetch("/api/v1/auth/csrf", { credentials: "same-origin" });
  if (!response.ok) throw new ApiError(response.status, "CSRF_UNAVAILABLE", "Cannot obtain CSRF token");
  const body = (await response.json()) as { csrfToken: string };
  csrfToken = body.csrfToken;
  return csrfToken;
}

async function request<T>(
  path: string,
  init: { method?: string; body?: unknown } = {},
): Promise<T> {
  const method = init.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET" && method !== "HEAD") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRFToken"] = await ensureCsrf();
  }
  const response = await fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (response.status === 204) return undefined as T;
  const data: unknown = await response.json();
  if (!response.ok) {
    const body = data as ApiErrorBody;
    throw new ApiError(response.status, body?.error?.code ?? "UNKNOWN", body?.error?.message ?? "Request failed");
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
  me: () => request<CurrentUser>("/api/v1/auth/me"),
  // Django rotates the CSRF token on login/logout — drop the cached token first.
  login: async (username: string, password: string) => {
    const user = await request<CurrentUser>("/api/v1/auth/login", {
      method: "POST",
      body: { username, password },
    });
    csrfToken = null;
    return user;
  },
  logout: async () => {
    const result = await request<{ status: string }>("/api/v1/auth/logout", { method: "POST" });
    csrfToken = null;
    return result;
  },
};
