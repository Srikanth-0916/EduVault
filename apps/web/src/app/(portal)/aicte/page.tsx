"use client";

import { ArrowRight, Building2, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { BarChart } from "@/components/charts/bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { NationalKpiGrid } from "@/components/aicte/national-kpi-grid";
import { IntakeVsEnrollment } from "@/components/aicte/intake-vs-enrollment";
import { ReviewQueueTable } from "@/components/aicte/review-queue-table";
import { RiskCallout } from "@/components/aicte/risk-callout";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useNationalDashboard } from "@/hooks/use-national-dashboard";
import { useReviewQueue } from "@/hooks/use-review";
import { ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

function NationalContent() {
  const [year, setYear] = useAcademicYear();
  const dashboard = useNationalDashboard(year);
  const queue = useReviewQueue("UNDER_AICTE_REVIEW");
  const data = dashboard.data;
  if (dashboard.isLoading) return <Skeleton className="h-96" />;
  if (dashboard.error || !data) return <EmptyState title="National dashboard unavailable" description={dashboard.error instanceof ApiError ? dashboard.error.message : "Could not load the national dashboard."} action={<Button variant="secondary" onClick={() => dashboard.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} />;
  return <div className="space-y-6">
    <PageHeader eyebrow="AICTE national console" title="National overview" description="Aggregate coverage, intake reconciliation and review backlog across synthetic institutions. Student-level fields remain scoped to the permitted review surfaces." actions={<Select aria-label="Academic year" value={year} onChange={(event) => setYear(event.target.value)} containerClassName="w-36"><option value="2025-26">2025-26</option><option value="2026-27">2026-27</option><option value="2027-28">2027-28</option></Select>} />
    <NationalKpiGrid kpis={data.kpis} />
    {data.possibleExcessProgrammes.length ? <RiskCallout title="Possible excess requires explanation, not automatic rejection.">Review the intake evidence and separate regular from authorized supernumerary allocations before deciding a submission.</RiskCallout> : null}
    <div className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
      <Card><CardHeader><CardTitle>Possible-excess programme signal</CardTitle><CardDescription>Reported counts compared with approved capacity.</CardDescription></CardHeader><CardContent className="pt-4"><IntakeVsEnrollment rows={data.possibleExcessProgrammes} /></CardContent></Card>
      <Card><CardHeader><CardTitle>Institution types</CardTitle><CardDescription>Configured synthetic institution directory.</CardDescription></CardHeader><CardContent className="pt-4"><DonutChart data={data.institutionTypeDistribution} centerLabel="institutions" /></CardContent></Card>
    </div>
    <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle>Review backlog</CardTitle><CardDescription>Submitted batches awaiting an AICTE decision.</CardDescription></div><Link href="/aicte/review" className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">Open queue <ArrowRight className="size-3.5" /></Link></CardHeader><CardContent className="pt-4">{queue.isLoading ? <Skeleton className="h-52" /> : queue.error ? <p className="text-sm text-danger">{queue.error instanceof ApiError ? queue.error.message : "Queue unavailable."}</p> : <ReviewQueueTable items={queue.data?.items.slice(0, 5) ?? []} />}</CardContent></Card>
      <Card><CardHeader><CardTitle>Batch status</CardTitle><CardDescription>Workflow distribution for current records.</CardDescription></CardHeader><CardContent className="pt-4"><BarChart data={data.batchStatusDistribution} /></CardContent></Card>
    </div>
    <Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle>Institution reporting</CardTitle><CardDescription>Batch activity and current enrolment coverage.</CardDescription></div><Link href="/aicte/institutions" className="text-xs font-semibold text-primary hover:underline">Directory</Link></CardHeader><CardContent className="pt-4"><div className="space-y-2">{data.reportingInstitutions.map((institution) => <Link key={institution.institutionId} href={`/aicte/institutions/${institution.institutionId}`} className="flex flex-wrap items-center justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5 hover:border-primary/35 hover:bg-surface-muted/35"><div className="flex items-center gap-2"><Building2 className="size-4 text-primary" /><div><p className="text-xs font-medium text-ink">{institution.institutionName}</p><p className="text-[11px] text-ink-soft/70">{institution.institutionType} · {institution.enrollmentCount} current enrolments</p></div></div><div className="flex items-center gap-3"><StatusBadge family="case" status={institution.reportingStatus === "REPORTING" ? "RESOLVED" : "OPEN"} label={institution.reportingStatus === "REPORTING" ? "Reporting" : "No batch"} /><span className="text-[11px] tabular text-ink-soft">{institution.batchCount} batch(es)</span></div></Link>)}</div></CardContent></Card>
    <p className="text-right text-[11px] text-ink-soft/70">{data.dataFreshness} Generated {formatDateTime(data.generatedAt)}</p>
  </div>;
}

export default function AicteOverviewPage() { return <Suspense fallback={<Skeleton className="h-96" />}><NationalContent /></Suspense>; }
