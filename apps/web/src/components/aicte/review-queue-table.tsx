import Link from "next/link";

import { ArrowRight } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ReviewQueueItem } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ReviewQueueTable({ items }: { items: ReviewQueueItem[] }) {
  if (!items.length) return <p className="rounded-[8px] border border-dashed border-border px-4 py-8 text-center text-xs text-ink-soft">No batches are waiting in this queue.</p>;
  return <div className="overflow-hidden rounded-[12px] border border-border bg-surface shadow-card"><Table><TableHeader><TableRow><TableHead>Batch / institution</TableHead><TableHead>Rows</TableHead><TableHead>Risk</TableHead><TableHead>Age</TableHead><TableHead>Submitted</TableHead><TableHead className="text-right">Open</TableHead></TableRow></TableHeader><TableBody>{items.map((item) => <TableRow key={item.batchId}><TableCell><Link href={`/aicte/review/${item.batchId}`} className="font-mono text-xs font-medium text-primary hover:underline">{item.batchId.slice(0, 14)}…</Link><p className="mt-0.5 text-xs text-ink-soft">{item.institutionName}</p><p className="text-[11px] text-ink-soft/65">{item.institutionId} · v{item.version}</p></TableCell><TableCell><p className="tabular text-sm font-medium text-ink">{item.rowCount}</p><p className="text-[11px] text-ink-soft/70">{item.blockingFindings} blocking</p></TableCell><TableCell>{item.severity ? <StatusBadge family="severity" status={item.severity} /> : <StatusBadge family="severity" status="INFO" />}</TableCell><TableCell><p className="tabular text-sm text-ink">{item.ageDays}d</p><p className="text-[11px] text-ink-soft/70">SLA watch</p></TableCell><TableCell className="text-xs text-ink-soft">{formatDateTime(item.submittedAt)}</TableCell><TableCell className="text-right"><Link href={`/aicte/review/${item.batchId}`} aria-label={`Review ${item.batchId}`}><ArrowRight className="ml-auto size-4 text-primary" /></Link></TableCell></TableRow>)}</TableBody></Table></div>;
}
