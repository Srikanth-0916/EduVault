import { ArrowRight, CalendarDays, Fingerprint, GitCompareArrows } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DuplicateCase } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";

function value(evidence: Record<string, unknown> | null, key: string): string | null {
  const item = evidence?.[key];
  return item === null || item === undefined || item === "" ? null : String(item);
}

export function CaseEvidence({ caseItem }: { caseItem: DuplicateCase }) {
  const evidence = caseItem.evidence ?? {};
  const overlap = value(evidence, "overlapDays");
  const transferContext = value(evidence, "transferContext");
  const responses = Array.isArray(evidence.institutionResponses) ? evidence.institutionResponses : [];
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Fingerprint className="size-4 text-primary" aria-hidden="true" />Identifier evidence</CardTitle></CardHeader>
        <CardContent className="space-y-3 pt-3">
          <div className="rounded-[8px] border border-border bg-surface-muted/35 p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">Masked APAAR</p><p className="mt-1 font-mono text-lg text-ink">{value(evidence, "maskedIdentifier") ?? (Array.isArray(evidence.maskedIdentifiers) ? evidence.maskedIdentifiers.join(" · ") : "Last four only")}</p></div>
          <dl className="space-y-2 text-xs">
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Match type</dt><dd><StatusBadge family="case" status={caseItem.matchType} label={titleCase(caseItem.matchType)} /></dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Existing record</dt><dd className="font-mono text-ink">{value(evidence, "existingEnrollmentId") ?? "Batch row match"}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Existing student ID</dt><dd className="text-ink">{value(evidence, "existingLocalId") ?? "—"}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Institution</dt><dd className="text-right text-ink">{value(evidence, "institutionName") ?? "Same batch / institution"}</dd></div>
          </dl>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><CalendarDays className="size-4 text-primary" aria-hidden="true" />Date context</CardTitle></CardHeader>
        <CardContent className="space-y-3 pt-3">
          <div className="flex items-center justify-between gap-3 rounded-[8px] border border-border bg-surface-muted/35 p-3 text-xs">
            <div><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Current row</p><p className="mt-1 text-ink">{value(evidence, "rowNumber") ? `Source row ${value(evidence, "rowNumber")}` : "Staged batch row"}</p></div>
            <ArrowRight className="size-4 text-ink-soft/40" aria-hidden="true" />
            <div className="text-right"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Existing row</p><p className="mt-1 text-ink">{formatDate(value(evidence, "admissionDate"))}</p></div>
          </div>
          <dl className="space-y-2 text-xs">
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Existing exit</dt><dd className="text-ink">{formatDate(value(evidence, "exitDate"))}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Overlap days</dt><dd className="font-semibold tabular text-ink">{overlap ?? "0"}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Transfer context</dt><dd><Badge tone={transferContext === "OVERLAP" ? "danger" : "info"}>{transferContext ? titleCase(transferContext) : "Review context"}</Badge></dd></div>
            <div className="flex justify-between gap-3"><dt className="text-ink-soft">Existing status</dt><dd className="text-ink">{value(evidence, "statusContext") ? titleCase(value(evidence, "statusContext") as string) : "—"}</dd></div>
          </dl>
        </CardContent>
      </Card>
      {responses.length ? (
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><GitCompareArrows className="size-4 text-primary" aria-hidden="true" />Institution responses</CardTitle></CardHeader>
          <CardContent className="space-y-2 pt-3">
            {responses.map((response, index) => {
              const item = response as { message?: string; by?: string; at?: string };
              return <div key={`${item.at ?? "response"}-${index}`} className="rounded-[8px] border border-border p-3"><p className="text-sm leading-6 text-ink">{item.message}</p><p className="mt-1 text-[11px] text-ink-soft/70">{item.by ?? "Institution"} · {item.at ?? ""}</p></div>;
            })}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
