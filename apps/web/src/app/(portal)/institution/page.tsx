"use client";

import {
  ArrowRight,
  ClipboardList,
  Plus,
  RefreshCw,
  UploadCloud,
  UserPlus,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense } from "react";

import { BarChart } from "@/components/charts/bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { KpiGrid } from "@/components/institution/kpi-grid";
import { CapacityBar } from "@/components/institution/capacity-bar";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useInstitutionDashboard } from "@/hooks/use-dashboard";
import { ApiError } from "@/lib/api";
import { formatDateTime, formatDate, titleCase } from "@/lib/utils";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-72" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.45fr_0.85fr]">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}

function InstitutionOverview() {
  const router = useRouter();
  const [year, setYear] = useAcademicYear();
  const dashboard = useInstitutionDashboard(year);
  const data = dashboard.data;

  if (dashboard.isLoading) return <DashboardSkeleton />;

  if (dashboard.error) {
    return (
      <div className="space-y-4">
        <PageHeader
          eyebrow="Institution workspace"
          title="Institution overview"
          description="Approved intake, reported enrolment, identity quality and open review cases."
        />
        <EmptyState
          title="Dashboard unavailable"
          description={
            dashboard.error instanceof ApiError
              ? dashboard.error.message
              : "The dashboard could not be loaded. Check that the API is running."
          }
          action={
            <Button variant="secondary" onClick={() => dashboard.refetch()} icon={<RefreshCw className="size-4" />}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Institution workspace"
        title={`${data.institutionName} overview`}
        description="Approved capacity and reported enrolment are shown separately. APAAR format validity, mock external checks and AICTE acceptance are never collapsed into one status."
        actions={
          <>
            <Select
              aria-label="Academic year"
              value={year}
              onChange={(event) => setYear(event.target.value)}
              containerClassName="w-36"
            >
              <option value="2025-26">2025-26</option>
              <option value="2026-27">2026-27</option>
              <option value="2027-28">2027-28</option>
            </Select>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => router.push("/institution/students/new")}
              icon={<UserPlus className="size-4" />}
            >
              Add student
            </Button>
            <Button
              size="sm"
              onClick={() => router.push("/institution/batches/new")}
              icon={<UploadCloud className="size-4" />}
            >
              New batch
            </Button>
          </>
        }
      />

      <KpiGrid kpis={data.kpis} />

      <div className="grid gap-4 xl:grid-cols-[1.45fr_0.85fr]">
        <Card className="overflow-hidden">
          <CardHeader className="flex-row items-start justify-between gap-3">
            <div>
              <CardTitle>Capacity by programme</CardTitle>
              <CardDescription>
                Regular and supernumerary allocations are separate; supernumerary
                admission never changes the classification of a regular seat.
              </CardDescription>
            </div>
            <Link
              href={`/institution/programmes?academicYear=${year}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
            >
              All programmes <ArrowRight className="size-3.5" aria-hidden="true" />
            </Link>
          </CardHeader>
          <CardContent className="px-0 pb-0 pt-4">
            {data.capacity.length ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Programme</TableHead>
                    <TableHead>Reported / approved</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.capacity.slice(0, 6).map((row) => (
                    <TableRow key={row.programmeId}>
                      <TableCell>
                        <p className="font-medium text-ink">{row.programmeName}</p>
                        <p className="text-xs text-ink-soft/70">
                          {row.programmeCode} · {row.campusName ?? "Campus"}
                        </p>
                      </TableCell>
                      <TableCell>
                        <CapacityBar
                          approvedRegular={row.approvedRegular}
                          approvedSupernumerary={row.approvedSupernumerary}
                          reportedRegular={row.reportedRegular}
                          reportedSupernumerary={row.reportedSupernumerary}
                          status={row.status}
                        />
                      </TableCell>
                      <TableCell>
                        <StatusBadge family="capacity" status={row.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="px-5 pb-5">
                <EmptyState
                  title="No programmes"
                  description="Active programmes and approved intake will appear here once configured."
                />
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Identity quality</CardTitle>
              <CardDescription>
                Format validity is not verification. Mock external checks are labelled.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <DonutChart data={data.identityDistribution} centerLabel="enrolments" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Enrolment status</CardTitle>
              <CardDescription>Current records for {year}.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <BarChart
                data={data.enrollmentStatusDistribution}
                emptyLabel="No current enrolments for this year."
              />
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Recent batches</CardTitle>
              <CardDescription>Upload, validation, attestation and review state.</CardDescription>
            </div>
            <Link
              href={`/institution/batches?academicYear=${year}`}
              className="text-xs font-semibold text-primary hover:underline"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {data.recentBatches.length ? (
              data.recentBatches.map((batch) => (
                <Link
                  key={batch.id}
                  href={`/institution/batches/${batch.id}`}
                  className="flex items-center justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5 transition-colors hover:border-primary/40 hover:bg-surface-muted/40"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-xs text-ink">{batch.id}</p>
                    <p className="mt-0.5 text-[11px] text-ink-soft/70">
                      {batch.rowCount} rows · v{batch.version} · {formatDate(batch.createdAt)}
                    </p>
                  </div>
                  <StatusBadge family="batch" status={batch.status} />
                </Link>
              ))
            ) : (
              <p className="rounded-[8px] border border-dashed border-border px-3 py-6 text-center text-xs text-ink-soft">
                No batches yet. Upload a CSV to begin.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Open cases</CardTitle>
              <CardDescription>Duplicate and cross-institution review.</CardDescription>
            </div>
            <Link
              href={`/institution/cases?academicYear=${year}`}
              className="text-xs font-semibold text-primary hover:underline"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {data.openCases.length ? (
              data.openCases.map((item) => (
                <Link
                  key={item.id}
                  href={`/institution/cases/${item.id}`}
                  className="flex items-center justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5 transition-colors hover:border-primary/40 hover:bg-surface-muted/40"
                >
                  <div>
                    <p className="text-xs font-medium text-ink">
                      {titleCase(item.matchType)}
                    </p>
                    <p className="mt-0.5 text-[11px] text-ink-soft/70">
                      Opened {formatDateTime(item.openedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge family="severity" status={item.severity} />
                    <StatusBadge family="case" status={item.status} />
                  </div>
                </Link>
              ))
            ) : (
              <p className="rounded-[8px] border border-dashed border-border px-3 py-6 text-center text-xs text-ink-soft">
                No open duplicate cases.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-[10px] border border-border bg-surface px-4 py-3 text-xs text-ink-soft">
        <ClipboardList className="size-4 text-primary" aria-hidden="true" />
        <span>{data.dataFreshness}</span>
        <span className="text-ink-soft/40" aria-hidden="true">·</span>
        <span>Generated {formatDateTime(data.generatedAt)}</span>
        <Link
          href={`/institution/batches/new?academicYear=${year}`}
          className="ml-auto inline-flex items-center gap-1 font-semibold text-primary hover:underline"
        >
          <Plus className="size-3.5" aria-hidden="true" /> Start a submission
        </Link>
      </div>
    </div>
  );
}

export default function InstitutionOverviewPage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <InstitutionOverview />
    </Suspense>
  );
}
