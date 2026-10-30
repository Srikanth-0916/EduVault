"use client";

import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/input";

const RESOLUTIONS = [
  ["VALID_TRANSFER", "Valid transfer"],
  ["PERMITTED_CONCURRENT_ENROLMENT", "Permitted concurrent enrolment"],
  ["DATA_ERROR", "Data error"],
  ["UNRESOLVED", "Unresolved"],
  ["POLICY_BREACH", "Policy breach"],
] as const;

export function ResolutionDialog({
  open,
  onOpenChange,
  loading,
  error,
  onResolve,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  loading: boolean;
  error: string | null;
  onResolve: (code: string, reason: string) => Promise<void>;
}) {
  const [code, setCode] = useState("VALID_TRANSFER");
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  return <Dialog open={open} onOpenChange={onOpenChange} title="Resolve duplicate case" description="Only a supervisor can confirm this outcome. The resolution is retained for audit and does not auto-delete or merge records." footer={<><Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button><Button disabled={!confirmed || reason.trim().length < 3} loading={loading} onClick={() => onResolve(code, reason.trim())}>Confirm resolution</Button></>}><div className="space-y-4"><Select label="Resolution outcome" value={code} onChange={(event) => setCode(event.target.value)}>{RESOLUTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select><Textarea label="Resolution reason" required value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Summarize the evidence reviewed and rationale." /><label className="flex items-start gap-2 rounded-[8px] border border-accent/25 bg-accent-soft/35 p-3 text-xs leading-5 text-[#92400e]"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} className="mt-1 size-4 accent-[var(--color-primary)]" /><span><AlertTriangle className="mr-1 inline size-3.5" />I confirm this human review outcome. It does not automatically cancel, merge, or label a record as fraud.</span></label>{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}</div></Dialog>;
}
