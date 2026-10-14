// SPDX-License-Identifier: Apache-2.0
import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError } from "../api/client";
import type { CurrentUser, Role } from "../api/types";
import { AuthContext } from "./context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch((error: unknown) => {
        if (!(error instanceof ApiError) || error.status !== 401) {
          // Non-401 failures leave us logged out but should not crash the app.
          setUser(null);
        }
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setUser(await api.login(username, password));
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (...roles: Role[]) => user !== null && roles.some((r) => user.roles.includes(r)),
    [user],
  );

  return <AuthContext.Provider value={{ user, loading, login, logout, hasRole }}>{children}</AuthContext.Provider>;
}
