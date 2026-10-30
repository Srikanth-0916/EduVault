"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import type { Programme } from "@/lib/types";

export interface IntakeSnapshotPayload {
  academicYear: string;
  approvalReference: string;
  validFrom: string;
  validTo: string | null;
  issuedBy: string | null;
  notes: string;
  allocations: {
    seatClassification: "APPROVED_REGULAR" | "APPROVED_SUPERNUMERARY";
    approvedCount: number;
    authorizationReference: string | null;
  }[];
}

export function IntakeForm({
  programme,
  academicYear,
  onSubmit,
  loading = false,
  error = null,
}: {
  programme: Programme;
  academicYear: string;
  onSubmit: (payload: IntakeSnapshotPayload) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}) {
  const [regular, setRegular] = useState(String(programme.approvedRegular));
  const [supernumerary, setSupernumerary] = useState(String(programme.approvedSupernumerary));
  const [approvalReference, setApprovalReference] = useState("");
  const [authorizationReference, setAuthorizationReference] = useState("");
  const [validFrom, setValidFrom] = useState("2026-04-01");
  const [validTo, setValidTo] = useState("");
  const [issuedBy, setIssuedBy] = useState("AICTE (synthetic demo)");
  const [reason, setReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);
    if (!approvalReference.trim()) {
      setLocalError("Approval reference is required.");
      return;
    }
    if (Number(supernumerary) > 0 && !authorizationReference.trim()) {
      setLocalError("An authorization reference is required for supernumerary seats.");
      return;
    }
    if (reason.trim().length < 3) {
      setLocalError("An audit reason is required.");
      return;
    }
    await onSubmit({
      academicYear,
      approvalReference: approvalReference.trim(),
      validFrom,
      validTo: validTo || null,
      issuedBy: issuedBy.trim() || null,
      notes: reason.trim(),
      allocations: [
        {
          seatClassification: "APPROVED_REGULAR",
          approvedCount: Number(regular),
          authorizationReference: null,
        },
        {
          seatClassification: "APPROVED_SUPERNUMERARY",
          approvedCount: Number(supernumerary),
          authorizationReference: authorizationReference.trim() || null,
        },
      ],
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Card className="border-primary/20 bg-primary-soft/25">
        <CardContent className="p-3 text-xs leading-5 text-[#115e59]">
          Creating a snapshot supersedes the previous active snapshot. Historical
          allocations remain immutable and are retained by version.
        </CardContent>
      </Card>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Regular approved seats" type="number" min={0} max={1000000} required value={regular} onChange={(event) => setRegular(event.target.value)} />
        <Input label="Authorized supernumerary seats" type="number" min={0} max={1000000} required value={supernumerary} onChange={(event) => setSupernumerary(event.target.value)} />
        <Input label="Approval reference" required value={approvalReference} onChange={(event) => setApprovalReference(event.target.value)} placeholder="AICTE/DEMO/2026-27/001" />
        <Input label="Authorization reference" required={Number(supernumerary) > 0} value={authorizationReference} onChange={(event) => setAuthorizationReference(event.target.value)} placeholder="Required when supernumerary seats are approved" hint="Supernumerary allocation remains separate from regular seats." />
        <Input label="Valid from" type="date" required value={validFrom} onChange={(event) => setValidFrom(event.target.value)} />
        <Input label="Valid to" type="date" value={validTo} onChange={(event) => setValidTo(event.target.value)} />
        <Input label="Issued by" value={issuedBy} onChange={(event) => setIssuedBy(event.target.value)} />
        <Input label="Academic year" value={academicYear} readOnly className="bg-surface-muted" />
      </div>
      <Textarea label="Audit reason / notes" required value={reason} onChange={(event) => setReason(event.target.value)} hint="This reason is stored in the audit event for the new snapshot." />
      {localError || error ? <p role="alert" className="text-sm text-danger">{localError ?? error}</p> : null}
      <div className="flex justify-end"><Button type="submit" loading={loading}>Create snapshot version</Button></div>
    </form>
  );
}
