"use client";

import { AlertTriangle, CheckCircle2, CornerDownLeft, XCircle } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/input";
import type { BatchDetail, Role } from "@/lib/types";

const REASON_CODES = [
  ["DATA_QUALITY", "Data quality"],
  ["INTAKE_EXCEPTION", "Intake exception"],
  ["IDENTITY_REVIEW", "Identity review"],
  ["POLICY", "Policy"],
  ["OTHER", "Other"],
] as const;

type Decision = "ACCEPT" | "RETURN" | "REJECT";

export function BatchDecisionPanel({
  batch,
  role,
  onDecision,
  loading = false,
  error = null,
}: {
  batch: BatchDetail;
  role: Role | string;
  onDecision: (decision: Decision, reasonCode: string, reason: string) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}) {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [reasonCode, setReasonCode] = useState("DATA_QUALITY");
  const [reason, setReason] = useState("");
  const canDecide = ["AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role);
  const isUnderReview = batch.status === "UNDER_AICTE_REVIEW";
  const confirmLabel = decision === "ACCEPT" ? "Confirm acceptance" : decision === "RETURN" ? "Confirm return" : "Confirm rejection";

  return (
    <div className="space-y-4 rounded-[12px] border border-border bg-surface p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-base font-semibold text-ink">Decision</h2>
          <p className="mt-1 text-xs leading-5 text-ink-soft">A decision changes workflow state; it does not edit student fields.</p>
        </div>
        <Badge tone="mock">Controlled review</Badge>
      </div>
      {batch.decision ? (
        <div className="rounded-[8px] border border-primary/20 bg-primary-soft/30 p-3 text-xs leading-5 text-ink-soft">
          Decision recorded: <strong className="text-ink">{batch.decision}</strong> · {batch.decisionReason ?? "No reason supplied."}
        </div>
      ) : null}
      {!canDecide ? <p className="rounded-[8px] bg-surface-muted/50 px-3 py-2 text-xs text-ink-soft">Reviewer or supervisor role required to record a decision.</p> : null}
      {canDecide && isUnderReview ? (
        <div className="grid gap-2 sm:grid-cols-3">
          <Button onClick={() => setDecision("ACCEPT")} icon={<CheckCircle2 className="size-4" />}>Accept</Button>
          <Button variant="secondary" onClick={() => setDecision("RETURN")} icon={<CornerDownLeft className="size-4" />}>Return for correction</Button>
          <Button variant="dangerOutline" onClick={() => setDecision("REJECT")} icon={<XCircle className="size-4" />}>Reject</Button>
        </div>
      ) : null}
      {!isUnderReview && canDecide ? <p className="rounded-[8px] bg-surface-muted/50 px-3 py-2 text-xs text-ink-soft">This batch is no longer under review. Illegal transitions are disabled.</p> : null}
      {error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}

      <Dialog
        open={Boolean(decision)}
        onOpenChange={(open) => !open && setDecision(null)}
        title={decision === "ACCEPT" ? "Accept batch" : decision === "RETURN" ? "Return batch for correction" : "Reject batch"}
        description="Institution will be notified. The reason becomes part of the audit and decision history."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDecision(null)}>Cancel</Button>
            <Button
              variant={decision === "REJECT" ? "danger" : "primary"}
              disabled={reason.trim().length < 3 || !reasonCode}
              loading={loading}
              onClick={() => decision && onDecision(decision, reasonCode, reason.trim())}
            >
              {confirmLabel}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-[8px] border border-accent/25 bg-accent-soft/35 px-3 py-2.5 text-xs leading-5 text-[#92400e]"><AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />The decision is recorded against the submitted batch version. It cannot be edited after submission.</div>
          <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink" htmlFor="decision-reason-code">Reason code<select id="decision-reason-code" value={reasonCode} onChange={(event) => setReasonCode(event.target.value)} className="h-11 rounded-[8px] border border-border bg-surface px-3 text-sm font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20">{REASON_CODES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <Textarea label="Decision reason" required value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Explain the decision for the institution and audit trail." />
        </div>
      </Dialog>
    </div>
  );
}
