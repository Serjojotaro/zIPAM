// SPDX-License-Identifier: Apache-2.0
import { createContext, useContext } from "react";
import type { CurrentUser, Role } from "../api/types";

export interface AuthState {
  user: CurrentUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: Role[]) => boolean;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (ctx === null) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
