import { Check, Circle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { BatchDetail } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function BatchTimeline({ batch }: { batch: BatchDetail }) {
  const events = [
    { label: "Batch created", value: batch.createdAt, done: true },
    { label: "Nodal attestation", value: batch.attestedAt, done: Boolean(batch.attestedAt) },
    { label: "Submitted to AICTE queue", value: batch.submittedAt, done: Boolean(batch.submittedAt) },
    { label: "Decision", value: batch.decidedAt, done: Boolean(batch.decidedAt), status: batch.decision },
  ];
  return (
    <ol className="space-y-3">
      {events.map((event) => (
        <li key={event.label} className="flex items-start gap-3">
          <span className={event.done ? "mt-0.5 flex size-5 items-center justify-center rounded-full bg-primary text-white" : "mt-0.5 flex size-5 items-center justify-center rounded-full border border-border text-ink-soft/40"}>
            {event.done ? <Check className="size-3" aria-hidden="true" /> : <Circle className="size-2.5" aria-hidden="true" />}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-medium text-ink">{event.label}</p>
            <p className="text-[11px] text-ink-soft/70">{formatDateTime(event.value)}</p>
          </div>
          {event.status ? <Badge tone={event.status === "ACCEPT" ? "success" : event.status === "RETURN" ? "warning" : "danger"}>{event.status}</Badge> : null}
        </li>
      ))}
    </ol>
  );
}
