"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";

const CLAIMS = [
  ["INSTITUTION", "Institution", "The institution that submitted the record"],
  ["PROGRAMME", "Programme", "The submitted programme name"],
  ["ACADEMIC_YEAR", "Academic year", "The record's academic year"],
  ["ENROLMENT_STATUS", "Enrolment status", "Current submitted enrolment state"],
  ["RECORD_ACCEPTANCE", "AICTE acceptance", "Whether the current record is accepted"],
  ["APAAR_FORMAT_STATUS", "APAAR format status", "Format check result only"],
  ["APAAR_EXTERNAL_STATUS", "APAAR external status", "Mock external status only"],
] as const;

export interface ShareWizardValues {
  recipientName: string;
  recipientOrg: string;
  recipientEmail: string;
  purpose: string;
  requestedClaims: string[];
  legalBasis: "CONSENT";
  expiresInHours: number;
  singleUse: boolean;
}

export function ShareWizard({
  open,
  onOpenChange,
  onSubmit,
  loading = false,
  error = null,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: ShareWizardValues) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}) {
  const [recipientName, setRecipientName] = useState("");
  const [recipientOrg, setRecipientOrg] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [purpose, setPurpose] = useState("");
  const [claims, setClaims] = useState<string[]>([]);
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [singleUse, setSingleUse] = useState(false);
  const [review, setReview] = useState(false);
  const canReview = claims.length > 0;

  function toggleClaim(claim: string) {
    setClaims((current) => current.includes(claim) ? current.filter((item) => item !== claim) : [...current, claim]);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={review ? "Review authorization" : "Create a verification share"}
      description={review ? "Check the recipient, purpose and exact fields before issuing the link." : "Choose a purpose-bound set of claims. The verifier cannot search for additional records."}
      footer={review ? <><Button variant="secondary" onClick={() => setReview(false)}>Back</Button><Button loading={loading} onClick={() => onSubmit({ recipientName, recipientOrg, recipientEmail, purpose, requestedClaims: claims, legalBasis: "CONSENT", expiresInHours, singleUse })}>Authorize share</Button></> : <><Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button><Button disabled={!canReview} onClick={() => setReview(true)}>Review authorization</Button></>}
    >
      {!review ? (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2"><Input label="Recipient name" required value={recipientName} onChange={(event) => setRecipientName(event.target.value)} placeholder="Acme HR" /><Input label="Organisation" required value={recipientOrg} onChange={(event) => setRecipientOrg(event.target.value)} placeholder="Acme Demo" /><Input label="Recipient email" required type="email" value={recipientEmail} onChange={(event) => setRecipientEmail(event.target.value)} placeholder="hr@example.org" /><Input label="Purpose" required value={purpose} onChange={(event) => setPurpose(event.target.value)} placeholder="Employment screening" /></div>
          <div><p className="mb-2 text-[13px] font-medium text-ink">Claims to share <span className="text-danger">*</span></p><div className="space-y-2">{CLAIMS.map(([value, label, description]) => <label key={value} className="flex items-start gap-3 rounded-[8px] border border-border px-3 py-2.5 text-sm hover:bg-surface-muted/35"><input type="checkbox" aria-label={label} checked={claims.includes(value)} onChange={() => toggleClaim(value)} className="mt-1 size-4 accent-[var(--color-primary)]" /><span><span className="font-medium text-ink">{label}</span><span className="mt-0.5 block text-xs text-ink-soft/75">{description}</span></span></label>)}</div></div>
          <div className="grid gap-3 sm:grid-cols-2"><Input label="Expires in hours" type="number" min={1} max={168} value={expiresInHours} onChange={(event) => setExpiresInHours(Number(event.target.value))} hint="Between 1 and 168 hours." /><label className="flex items-center gap-2 pt-6 text-sm text-ink"><input type="checkbox" checked={singleUse} onChange={(event) => setSingleUse(event.target.checked)} className="size-4 accent-[var(--color-primary)]" />Single-use link</label></div>
          <p className="text-xs leading-5 text-ink-soft">The disclosure will show source and status for each claim. Full APAAR and student name are never allowed claims.</p>
          {error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}
        </div>
      ) : (
        <div className="space-y-3"><div className="rounded-[8px] border border-border bg-surface-muted/35 p-3 text-sm text-ink"><p className="font-medium">{recipientName} · {recipientOrg}</p><p className="mt-1 text-xs text-ink-soft">{recipientEmail} · {purpose}</p></div><div className="flex flex-wrap gap-1.5">{claims.map((claim) => <span key={claim} className="rounded-full bg-primary-soft px-2 py-1 font-mono text-[10px] text-primary">{claim}</span>)}</div><Textarea label="Consent notice" value="I authorize this recipient to view only the selected claims for the stated purpose." readOnly className="bg-surface-muted" /></div>
      )}
    </Dialog>
  );
}
