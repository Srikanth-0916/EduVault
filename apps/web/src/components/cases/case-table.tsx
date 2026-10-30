import Link from "next/link";

import { ArrowRight } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DuplicateCase } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

export function CaseTable({ cases, basePath }: { cases: DuplicateCase[]; basePath: string }) {
  if (!cases.length) return <EmptyState title="No cases" description="No duplicate or overlap cases match the selected filters." />;
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-surface shadow-card">
      <Table>
        <TableHeader><TableRow><TableHead>Case</TableHead><TableHead>Match</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead><TableHead>Opened</TableHead><TableHead className="text-right">Open</TableHead></TableRow></TableHeader>
        <TableBody>
          {cases.map((caseItem) => (
            <TableRow key={caseItem.id}>
              <TableCell><Link href={`${basePath}/${caseItem.id}`} className="font-mono text-xs font-medium text-primary hover:underline">{caseItem.id.slice(0, 12)}…</Link><p className="mt-0.5 text-[11px] text-ink-soft/70">{caseItem.discoveredBatchId ?? "Manual review"}</p></TableCell>
              <TableCell><p className="text-xs font-medium text-ink">{titleCase(caseItem.matchType)}</p><p className="text-[11px] text-ink-soft/70">{caseItem.evidence?.institutionName ? String(caseItem.evidence.institutionName) : "Protected identifier match"}</p></TableCell>
              <TableCell><StatusBadge family="severity" status={caseItem.severity} /></TableCell>
              <TableCell><StatusBadge family="case" status={caseItem.status} /></TableCell>
              <TableCell className="text-xs text-ink-soft">{formatDateTime(caseItem.openedAt)}</TableCell>
              <TableCell className="text-right"><Link href={`${basePath}/${caseItem.id}`} aria-label={`Open case ${caseItem.id}`}><ArrowRight className="ml-auto size-4 text-primary" /></Link></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
