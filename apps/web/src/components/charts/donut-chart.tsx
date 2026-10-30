"use client";

import { useId } from "react";

import { cn } from "@/lib/utils";

const PALETTE = ["#0f766e", "#14b8a6", "#f59e0b", "#b42318", "#64748b", "#7c3aed"];

export interface DonutDatum {
  key: string;
  label: string;
  count: number;
}

export function DonutChart({
  data,
  centerLabel,
  className,
}: {
  data: DonutDatum[];
  centerLabel?: string;
  className?: string;
}) {
  const id = useId();
  const total = data.reduce((sum, item) => sum + item.count, 0);
  let offset = 0;
  const stops = data.map((item, index) => {
    const start = total ? (offset / total) * 100 : 0;
    offset += item.count;
    const end = total ? (offset / total) * 100 : 0;
    return `${PALETTE[index % PALETTE.length]} ${start}% ${end}%`;
  });
  const background = total
    ? `conic-gradient(${stops.join(", ")})`
    : "conic-gradient(#e2e8f0 0% 100%)";

  return (
    <div className={cn("flex flex-col items-center gap-5 sm:flex-row", className)}>
      <div
        className="relative size-36 shrink-0 rounded-full"
        style={{ background }}
        role="img"
        aria-labelledby={`${id}-label`}
        aria-describedby={`${id}-legend`}
      >
        <div className="absolute inset-[18px] flex flex-col items-center justify-center rounded-full bg-surface text-center">
          <span className="font-display text-2xl font-semibold tabular text-ink">{total}</span>
          <span className="px-2 text-[10px] font-medium uppercase tracking-[0.07em] text-ink-soft/70">
            {centerLabel ?? "records"}
          </span>
        </div>
      </div>
      <div id={`${id}-legend`} className="w-full space-y-2">
        <p id={`${id}-label`} className="sr-only">
          Distribution across {data.length} statuses
        </p>
        {data.length ? (
          data.map((item, index) => (
            <div key={item.key} className="flex items-center justify-between gap-3 text-xs">
              <span className="flex min-w-0 items-center gap-2 text-ink-soft">
                <span
                  className="size-2 shrink-0 rounded-full"
                  style={{ background: PALETTE[index % PALETTE.length] }}
                  aria-hidden="true"
                />
                <span className="truncate">{item.label}</span>
              </span>
              <span className="font-medium tabular text-ink">{item.count}</span>
            </div>
          ))
        ) : (
          <p className="text-xs text-ink-soft/70">No records for this academic year.</p>
        )}
      </div>
    </div>
  );
}
