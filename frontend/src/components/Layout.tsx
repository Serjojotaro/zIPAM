// SPDX-License-Identifier: Apache-2.0
import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/context";

const NAV_ITEMS = [
  { to: "/organizations", label: "Organizations" },
  { to: "/tenants", label: "Tenants" },
  { to: "/regions", label: "Regions" },
  { to: "/sites", label: "Sites" },
];

export function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <p className="p-8 text-zinc-400">Loading…</p>;
  if (user === null) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function Layout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const canWrite = hasRole("operator", "admin");

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100">
      <aside className="flex w-56 flex-col gap-1 border-r border-zinc-800 p-4">
        <div className="mb-4 text-xl font-semibold tracking-tight">zIPAM</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `rounded px-3 py-1.5 text-sm ${
                isActive ? "bg-zinc-800 text-white" : "text-zinc-400 hover:bg-zinc-900"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
        <div className="mt-auto text-xs text-zinc-500">
          <div>
            {user?.username} · {user?.roles.join(", ")}
          </div>
          <div className="mt-1">{canWrite ? "write access" : "read-only"}</div>
        </div>
        <button
          type="button"
          className="mt-2 rounded border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-900"
          onClick={() => {
            void logout().then(() => navigate("/login"));
          }}
        >
          Log out
        </button>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
