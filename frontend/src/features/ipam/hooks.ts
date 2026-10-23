// SPDX-License-Identifier: Apache-2.0
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";

export function buildQuery(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") sp.set(key, String(value));
  }
  const qs = sp.toString();
  return qs === "" ? "" : `?${qs}`;
}

export function errorText(e: unknown): string {
  return e instanceof ApiError ? `${e.code}: ${e.message}` : "Request failed";
}

export interface Resource<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/** Fetches `path` (null = skip) and re-fetches on path change or reload(). */
export function useResource<T>(path: string | null): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    if (path === null) return;
    let active = true;
    setLoading(true);
    api.get<T>(path).then(
      (result) => {
        if (!active) return;
        setData(result);
        setError(null);
        setLoading(false);
      },
      (e: unknown) => {
        if (!active) return;
        setError(errorText(e));
        setLoading(false);
      },
    );
    return () => {
      active = false;
    };
  }, [path, nonce]);

  return { data, error, loading, reload };
}
