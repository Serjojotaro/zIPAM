// SPDX-License-Identifier: Apache-2.0
import type { Utilization } from "../../api/types";

export function UtilizationBar({ util }: { util: Utilization | null }) {
  if (util === null) return null;
  const percent = Math.min(100, Math.max(0, util.utilization_percent));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-zinc-400">
        <span>
          {util.allocated} / {util.total} allocated · {util.available} available
        </span>
        <span>{util.utilization_percent}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="h-2 w-full overflow-hidden rounded bg-zinc-800"
      >
        <div className="h-full bg-emerald-500" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
