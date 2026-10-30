"use client";

import { RefreshCw, Scale } from "lucide-react";
import { Suspense, useState } from "react";

import { CaseTable } from "@/components/cases/case-table";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useCases } from "@/hooks/use-cases";
import { ApiError } from "@/lib/api";

function NationalCasesContent() {
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const query = useCases({ status: status || undefined, severity: severity || undefined });
  return <div className="space-y-5"><PageHeader eyebrow="National oversight" title="Duplicate & overlap cases" description="Case evidence supports human review. A match is not an automatic rejection, merge or fraud determination." /><Card className="border-accent/25 bg-accent-soft/30"><CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#92400e]"><Scale className="mt-0.5 size-4 shrink-0" /><p>Cross-institution non-overlap may indicate a transfer. Resolution requires supervisor confirmation; request information to collect institution context.</p></CardContent></Card><Card><CardContent className="grid gap-3 p-4 sm:grid-cols-2"><Select aria-label="Filter case status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option value="OPEN">Open</option><option value="IN_REVIEW">In review</option><option value="RESOLVED">Resolved</option><option value="WITHDRAWN">Withdrawn</option></Select><Select aria-label="Filter case severity" value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="">All severities</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="WARNING">Warning</option><option value="LOW">Low</option><option value="INFO">Info</option></Select></CardContent></Card>{query.isLoading ? <Skeleton className="h-80" /> : query.error ? <EmptyState title="Cases unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load national cases."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : <><p className="text-xs text-ink-soft">{query.data?.total ?? 0} case(s)</p><CaseTable cases={query.data?.items ?? []} basePath="/aicte/cases" /></>}</div>;
}

export default function AicteCasesPage() { return <Suspense fallback={<Skeleton className="h-80" />}><NationalCasesContent /></Suspense>; }
