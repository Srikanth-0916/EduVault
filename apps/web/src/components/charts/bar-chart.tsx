"use client";

import { cn } from "@/lib/utils";

export interface BarDatum {
  key: string;
  label: string;
  count: number;
}

export function BarChart({
  data,
  className,
  emptyLabel = "No records",
}: {
  data: BarDatum[];
  className?: string;
  emptyLabel?: string;
}) {
  const max = Math.max(1, ...data.map((item) => item.count));
  if (!data.length) {
    return <p className={cn("text-xs text-ink-soft/70", className)}>{emptyLabel}</p>;
  }
  return (
    <div className={cn("space-y-3", className)}>
      {data.map((item) => (
        <div key={item.key}>
          <div className="mb-1 flex items-center justify-between gap-3 text-xs">
            <span className="text-ink-soft">{item.label}</span>
            <span className="font-medium tabular text-ink">{item.count}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${Math.max(2, (item.count / max) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
