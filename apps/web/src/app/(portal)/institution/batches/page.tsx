"use client";

import { ArrowRight, FilePlus2, RefreshCw, UploadCloud } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useBatches } from "@/hooks/use-batches";
import { ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

function BatchesContent() {
  const [year, setYear] = useAcademicYear();
  const batches = useBatches(year);
  const rows = batches.data?.items ?? [];

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Submission workflow"
        title="Batches"
        description="Upload, validate, attest and track CSV submissions. Every batch retains a checksum, validation run and decision trail."
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
            <Link href={`/institution/batches/new?academicYear=${year}`}>
              <Button size="sm" icon={<FilePlus2 className="size-4" />}>
                New batch
              </Button>
            </Link>
          </>
        }
      />

      <Card className="border-primary/20 bg-primary-soft/25">
        <CardContent className="flex flex-wrap items-center gap-3 p-4 text-xs leading-5 text-[#115e59]">
          <UploadCloud className="size-4 shrink-0" aria-hidden="true" />
          <span>
            CSV uploads are limited to 5 MB and 10,000 rows. Blocking validation errors must be corrected before attestation; advisory warnings remain visible and do not automatically reject a submission.
          </span>
          <a
            href="/api/v1/template.csv"
            className="ml-auto shrink-0 font-semibold text-primary underline-offset-4 hover:underline"
          >
            Download template
          </a>
        </CardContent>
      </Card>

      {batches.isLoading ? (
        <Skeleton className="h-96" />
      ) : batches.error ? (
        <EmptyState
          title="Batches unavailable"
          description={batches.error instanceof ApiError ? batches.error.message : "Could not load batches."}
          action={<Button variant="secondary" onClick={() => batches.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>}
        />
      ) : rows.length ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-ink-soft">
            <p>{batches.data?.total.toLocaleString("en-IN")} batch{batches.data?.total === 1 ? "" : "es"} for {year}</p>
            <p className="hidden sm:block">Synthetic data · mock APAAR integration</p>
          </div>
          {rows.map((batch) => {
            const summary = batch.summary;
            const errors = typeof summary.errorRows === "number" ? summary.errorRows : 0;
            const warnings = typeof summary.warningRows === "number" ? summary.warningRows : 0;
            return (
              <Link
                key={batch.id}
                href={`/institution/batches/${batch.id}`}
                className="group block rounded-[12px] border border-border bg-surface p-4 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-pop"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-mono text-sm font-medium text-ink">{batch.id}</p>
                      <StatusBadge family="batch" status={batch.status} />
                      {batch.decision ? <StatusBadge family="case" status={batch.decision === "ACCEPT" ? "RESOLVED" : batch.decision === "RETURN" ? "IN_REVIEW" : "OPEN"} label={`Decision: ${batch.decision}`} /> : null}
                    </div>
                    <p className="mt-1 text-xs text-ink-soft/75">
                      {batch.fileName ?? "No file uploaded"} · version {batch.version} · created {formatDateTime(batch.createdAt)}
                    </p>
                  </div>
                  <div className="grid grid-cols-3 gap-5 text-right">
                    <div><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/60">Rows</p><p className="mt-1 text-sm font-semibold tabular text-ink">{batch.rowCount ?? 0}</p></div>
                    <div><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/60">Warnings</p><p className="mt-1 text-sm font-semibold tabular text-accent">{warnings}</p></div>
                    <div><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/60">Errors</p><p className="mt-1 text-sm font-semibold tabular text-danger">{errors}</p></div>
                  </div>
                  <ArrowRight className="hidden size-4 shrink-0 text-ink-soft/40 transition-transform group-hover:translate-x-1 lg:block" aria-hidden="true" />
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={<FilePlus2 className="size-5" />}
          title="No batches yet"
          description="Start a batch to upload synthetic student data and run the validation rules."
          action={<Link href="/institution/batches/new"><Button icon={<UploadCloud className="size-4" />}>Create first batch</Button></Link>}
        />
      )}
    </div>
  );
}

export default function InstitutionBatchesPage() {
  return <Suspense fallback={<Skeleton className="h-96" />}><BatchesContent /></Suspense>;
}
