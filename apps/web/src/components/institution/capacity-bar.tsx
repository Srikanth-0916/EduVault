import { StatusBadge } from "@/components/status-badge";
import { cn } from "@/lib/utils";

function CapacityTrack({
  label,
  approved,
  reported,
  tone,
}: {
  label: string;
  approved: number;
  reported: number;
  tone: "regular" | "super";
}) {
  const pct = approved > 0 ? Math.min(100, (reported / approved) * 100) : reported > 0 ? 100 : 0;
  const overflow = approved > 0 && reported > approved;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-[11px]">
        <span className="font-medium text-ink-soft">{label}</span>
        <span className="tabular text-ink-soft/80">
          {reported} / {approved}
        </span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full bg-surface-muted"
        role="img"
        aria-label={`${label}: ${reported} reported of ${approved} approved`}
      >
        <div
          className={cn(
            "h-full rounded-full",
            overflow ? "bg-accent" : tone === "regular" ? "bg-primary" : "bg-[#14b8a6]",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function CapacityBar({
  approvedRegular,
  approvedSupernumerary,
  reportedRegular,
  reportedSupernumerary,
  status,
}: {
  approvedRegular: number;
  approvedSupernumerary: number;
  reportedRegular: number;
  reportedSupernumerary: number;
  status: string;
}) {
  return (
    <div className="min-w-52 space-y-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-soft/70">
          Capacity
        </span>
        <StatusBadge family="capacity" status={status} />
      </div>
      <CapacityTrack
        label="Regular"
        approved={approvedRegular}
        reported={reportedRegular}
        tone="regular"
      />
      <CapacityTrack
        label="Supernumerary"
        approved={approvedSupernumerary}
        reported={reportedSupernumerary}
        tone="super"
      />
    </div>
  );
}
