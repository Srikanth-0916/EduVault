import { CheckCircle2, Download } from "lucide-react";

import { ClaimCard } from "@/components/verify/claim-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PublicVerificationData } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function VerificationResult({ data }: { data: PublicVerificationData }) {
  function downloadReceipt() {
    if (!data.receipt) return;
    const blob = new Blob([JSON.stringify(data.receipt, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "verification-receipt.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  return <div className="space-y-5"><div className="flex flex-wrap items-start justify-between gap-3 rounded-[12px] border border-success/30 bg-success-soft/40 p-5"><div className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 size-5 text-success" aria-hidden="true" /><div><p className="font-display text-lg font-semibold text-ink">Verification link is valid</p><p className="mt-1 text-sm text-ink-soft">Only the claims authorized for this purpose are shown.</p></div></div><Badge tone="success">Valid until {formatDateTime(data.expiresAt)}</Badge></div><div className="grid gap-3">{data.claims.map((claim) => <ClaimCard key={claim.key} claim={claim} />)}</div><div className="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-dashed border-accent/35 bg-accent-soft/30 p-4 text-xs leading-5 text-[#92400e]"><p>{data.demoNotice}</p>{data.receipt ? <Button variant="secondary" size="sm" onClick={downloadReceipt} icon={<Download className="size-3.5" />}>Receipt JSON</Button> : null}</div></div>;
}
