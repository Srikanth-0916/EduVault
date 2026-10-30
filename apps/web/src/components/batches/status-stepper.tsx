import { Check, Circle, X } from "lucide-react";

import { cn } from "@/lib/utils";

const STEPS = [
  { key: "DRAFT", label: "Draft" },
  { key: "VALIDATION", label: "Validation" },
  { key: "ATTESTATION", label: "Attestation" },
  { key: "REVIEW", label: "AICTE review" },
  { key: "DECISION", label: "Decision" },
] as const;

function currentStep(status: string): number {
  if (status === "DRAFT") return 0;
  if (status === "VALIDATION_FAILED") return 1;
  if (status === "READY_FOR_ATTESTATION") return 2;
  if (status === "UNDER_AICTE_REVIEW" || status === "SUBMITTED") return 3;
  return 4;
}

export function StatusStepper({ status }: { status: string }) {
  const active = currentStep(status);
  const failed = status === "VALIDATION_FAILED" || status === "REJECTED";
  const returned = status === "RETURNED_FOR_CORRECTION";

  return (
    <ol className="grid gap-3 sm:grid-cols-5" aria-label="Batch progress">
      {STEPS.map((step, index) => {
        const complete = index < active || status === "ACCEPTED";
        const current = index === active;
        return (
          <li key={step.key} className="flex items-start gap-2">
            <span
              className={cn(
                "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border text-[10px] font-semibold",
                complete && "border-primary bg-primary text-white",
                current && !failed && !returned && "border-primary bg-primary-soft text-primary",
                current && failed && "border-danger bg-danger-soft text-danger",
                current && returned && "border-accent bg-accent-soft text-accent",
                !complete && !current && "border-border bg-surface text-ink-soft/50",
              )}
              aria-hidden="true"
            >
              {complete ? (
                <Check className="size-3" />
              ) : current && failed ? (
                <X className="size-3" />
              ) : (
                <Circle className="size-2.5 fill-current" />
              )}
            </span>
            <div className="min-w-0">
              <p
                className={cn(
                  "text-xs font-medium",
                  current ? "text-ink" : complete ? "text-ink-soft" : "text-ink-soft/55",
                )}
              >
                {step.label}
              </p>
              {current ? (
                <p className="text-[10px] text-ink-soft/65">
                  {index === 0
                    ? "Build and upload"
                    : index === 1
                      ? failed
                        ? "Correction needed"
                        : "Rules applied"
                      : index === 2
                        ? "Nodal declaration"
                        : index === 3
                          ? "AICTE queue"
                          : "Final outcome"}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
