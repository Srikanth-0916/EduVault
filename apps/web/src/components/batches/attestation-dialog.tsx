"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { BatchDetail } from "@/lib/types";

export function AttestationDialog({
  batch,
  open,
  onOpenChange,
  onAttest,
  loading,
  error,
}: {
  batch: BatchDetail;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAttest: (name: string) => Promise<void>;
  loading: boolean;
  error: string | null;
}) {
  const [name, setName] = useState("");
  const [declaration, setDeclaration] = useState(false);
  const canConfirm = declaration && name.trim().length >= 2;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Attest and submit batch"
      description="This declaration records that the institution has reviewed the staged rows and understands the synthetic demo data boundary."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            disabled={!canConfirm}
            loading={loading}
            onClick={() => onAttest(name.trim())}
          >
            Confirm attestation
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input
          label="Attesting nodal officer"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Full name"
        />
        <label className="flex items-start gap-3 rounded-[8px] border border-border bg-surface-muted/35 p-3 text-sm leading-5 text-ink">
          <input
            type="checkbox"
            checked={declaration}
            onChange={(event) => setDeclaration(event.target.checked)}
            className="mt-1 size-4 accent-[var(--color-primary)]"
          />
          <span>
            I confirm that the institution has reviewed the validation results,
            will correct blocking errors, and is submitting synthetic prototype
            data for controlled review.
          </span>
        </label>
        <div className="rounded-[8px] border border-accent/25 bg-accent-soft/35 px-3 py-2.5 text-xs leading-5 text-[#92400e]">
          Batch {batch.id} · {batch.rowCount ?? 0} rows · {batch.fileName ?? "CSV upload"}
        </div>
        {error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}
      </div>
    </Dialog>
  );
}
