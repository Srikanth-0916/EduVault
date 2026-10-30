"use client";

import { RefreshCw, Scale, ShieldAlert } from "lucide-react";
import Link from "next/link";
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

function CasesContent() {
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const cases = useCases({ status: status || undefined, severity: severity || undefined });
  const rows = cases.data?.items ?? [];
  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Review cases"
        title="Duplicate & overlap cases"
        description="Cases are review work items, not automatic rejection decisions. Evidence shows masked identifiers, date context and transfer context."
        actions={<Link href="/institution/batches"><Button variant="secondary" size="sm">View batches</Button></Link>}
      />
      <Card className="border-accent/25 bg-accent-soft/30">
        <CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#92400e]"><ShieldAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" /><p>APAAR is never shown in full. A cross-institution match may be a valid transfer when dates do not overlap; respond with context for the reviewer.</p></CardContent>
      </Card>
      <Card><CardContent className="flex flex-wrap items-center justify-between gap-3 p-4"><div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-ink-soft/70"><Scale className="size-3.5" aria-hidden="true" />Case filters</div><div className="flex gap-2"><Select aria-label="Filter case status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option value="OPEN">Open</option><option value="IN_REVIEW">In review</option><option value="RESOLVED">Resolved</option></Select><Select aria-label="Filter case severity" value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="">All severities</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="LOW">Low</option><option value="WARNING">Warning</option><option value="INFO">Info</option></Select></div></CardContent></Card>
      {cases.isLoading ? <Skeleton className="h-80" /> : cases.error ? <EmptyState title="Cases unavailable" description={cases.error instanceof ApiError ? cases.error.message : "Could not load cases."} action={<Button variant="secondary" onClick={() => cases.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : <><div className="flex justify-between text-xs text-ink-soft"><p>{cases.data?.total ?? 0} case{cases.data?.total === 1 ? "" : "s"}</p><p>Institution-scoped</p></div><CaseTable cases={rows} basePath="/institution/cases" /></>}
    </div>
  );
}

export default function InstitutionCasesPage() {
  return <Suspense fallback={<Skeleton className="h-80" />}><CasesContent /></Suspense>;
}
