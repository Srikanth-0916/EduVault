"use client";

import { CheckCircle2, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import type { BatchReceipt } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ReceiptDialog({
  receipt,
  open,
  onOpenChange,
}: {
  receipt: BatchReceipt | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  function download() {
    if (!receipt) return;
    const blob = new Blob([JSON.stringify(receipt, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${receipt.batchId}-receipt.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Submission receipt"
      description="The receipt is a signed prototype acknowledgement of the submitted file checksum."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>Close</Button>
          <Button icon={<Download className="size-4" />} onClick={download} disabled={!receipt}>
            Download JSON
          </Button>
        </>
      }
    >
      {receipt ? (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-[10px] border border-success/25 bg-success-soft/35 p-4">
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-success" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold text-ink">Receipt issued</p>
              <p className="mt-1 text-xs leading-5 text-ink-soft">
                Submitted {formatDateTime(receipt.submittedAt)} · {receipt.rowCount} rows
              </p>
            </div>
          </div>
          <dl className="space-y-2 rounded-[8px] border border-border p-3 text-xs">
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Batch</dt><dd className="font-mono text-ink">{receipt.batchId}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Checksum</dt><dd className="max-w-[70%] break-all text-right font-mono text-ink">{receipt.checksum}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Signature</dt><dd className="font-mono text-ink">{receipt.signature.signature?.slice(0, 16)}…</dd></div>
          </dl>
          <p className="text-[11px] leading-5 text-ink-soft/75">
            This is not a government certificate or live APAAR verification. It records the file identity and workflow submission only.
          </p>
        </div>
      ) : null}
    </Dialog>
  );
}
