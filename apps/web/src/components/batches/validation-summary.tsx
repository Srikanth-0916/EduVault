import { AlertTriangle, CheckCircle2, FileWarning, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function numberValue(summary: Record<string, unknown> | null | undefined, key: string): number {
  const value = summary?.[key];
  return typeof value === "number" ? value : 0;
}

export function ValidationSummary({
  summary,
  className,
}: {
  summary: Record<string, unknown> | null | undefined;
  className?: string;
}) {
  const total = numberValue(summary, "totalRows");
  const valid = numberValue(summary, "validRows");
  const warnings = numberValue(summary, "warningRows");
  const errors = numberValue(summary, "errorRows");
  const blocking = numberValue(summary, "blockingFindings");
  const findings = numberValue(summary, "findings");
  const byRule =
    summary && typeof summary.byRule === "object" && summary.byRule !== null
      ? (summary.byRule as Record<string, number>)
      : {};
  const validPct = total ? Math.round((valid / total) * 100) : 0;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="space-y-4 p-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-[8px] border border-border bg-surface-muted/35 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">Rows</p>
            <p className="mt-0.5 font-display text-xl font-semibold tabular text-ink">{total}</p>
          </div>
          <div className="rounded-[8px] border border-success/25 bg-success-soft/35 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-success">Valid</p>
            <p className="mt-0.5 font-display text-xl font-semibold tabular text-success">{valid}</p>
          </div>
          <div className="rounded-[8px] border border-accent/25 bg-accent-soft/45 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-accent">Warnings</p>
            <p className="mt-0.5 font-display text-xl font-semibold tabular text-accent">{warnings}</p>
          </div>
          <div className="rounded-[8px] border border-danger/25 bg-danger-soft/45 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-danger">Errors</p>
            <p className="mt-0.5 font-display text-xl font-semibold tabular text-danger">{errors}</p>
          </div>
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between text-[11px] text-ink-soft">
            <span>Row readiness</span>
            <span className="tabular">{validPct}% valid</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${validPct}%` }}
              role="progressbar"
              aria-valuenow={validPct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Valid row percentage"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[11px] text-ink-soft">
          <Badge tone={blocking ? "danger" : "success"}>
            {blocking ? <ShieldAlert className="size-3" aria-hidden="true" /> : <CheckCircle2 className="size-3" aria-hidden="true" />}
            {blocking ? `${blocking} blocking finding${blocking === 1 ? "" : "s"}` : "No blocking findings"}
          </Badge>
          <Badge tone="neutral">
            <FileWarning className="size-3" aria-hidden="true" /> {findings} total findings
          </Badge>
          {warnings ? (
            <Badge tone="warning">
              <AlertTriangle className="size-3" aria-hidden="true" /> Warnings still submit
            </Badge>
          ) : null}
        </div>

        {Object.keys(byRule).length ? (
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(byRule).map(([rule, count]) => (
              <span
                key={rule}
                className="rounded-full border border-border bg-surface px-2 py-0.5 font-mono text-[10px] text-ink-soft"
              >
                {rule}: {count}
              </span>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
