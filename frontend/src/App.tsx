// SPDX-License-Identifier: Apache-2.0
import { useEffect, useState } from "react";

type BackendStatus = "checking" | "ok" | "down";

async function checkHealth(): Promise<BackendStatus> {
  try {
    const response = await fetch("/health");
    if (!response.ok) return "down";
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "status" in body && body.status === "ok") {
      return "ok";
    }
    return "down";
  } catch {
    return "down";
  }
}

export default function App() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    void checkHealth().then(setStatus);
  }, []);

  const statusLabel = {
    checking: "Checking backend…",
    ok: "Backend: OK",
    down: "Backend: unreachable",
  }[status];

  const statusColor = {
    checking: "text-zinc-400",
    ok: "text-emerald-500",
    down: "text-red-500",
  }[status];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-950 text-zinc-100">
      <h1 className="text-3xl font-semibold tracking-tight">zIPAM</h1>
      <p className="text-zinc-400">IP Address Management — skeleton build</p>
      <p className={`font-mono text-sm ${statusColor}`} role="status">
        {statusLabel}
      </p>
    </main>
  );
}
