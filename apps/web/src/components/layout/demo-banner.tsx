import { FlaskConical } from "lucide-react";

export function DemoBanner() {
  return (
    <div
      role="note"
      className="no-print flex min-h-8 items-center justify-center gap-2 border-b border-amber-300/70 bg-accent-soft px-3 py-1.5 text-center text-[11px] font-semibold leading-5 tracking-wide text-[#92400e]"
    >
      <FlaskConical className="size-3.5 shrink-0" aria-hidden="true" />
      <span>
        Synthetic demo data <span aria-hidden="true">·</span> Mock integrations
        <span className="hidden sm:inline"> · Not for real student data</span>
      </span>
    </div>
  );
}
