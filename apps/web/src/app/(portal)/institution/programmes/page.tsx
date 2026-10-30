"use client";

import { BookOpen, Info, RefreshCw } from "lucide-react";
import { Suspense } from "react";

import { ProgrammeTable } from "@/components/institution/programme-table";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, StatCard } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useMyProgrammes } from "@/hooks/use-master-data";
import { ApiError } from "@/lib/api";

function ProgrammesContent() {
  const [year, setYear] = useAcademicYear();
  const programmes = useMyProgrammes(year);
  const rows = programmes.data ?? [];
  const approvedRegular = rows.reduce((sum, item) => sum + item.approvedRegular, 0);
  const approvedSuper = rows.reduce((sum, item) => sum + item.approvedSupernumerary, 0);
  const reported = rows.reduce(
    (sum, item) => sum + item.reportedRegular + item.reportedSupernumerary,
    0,
  );
  const possibleExcess = rows.filter((item) => item.capacityStatus === "POSSIBLE_EXCESS").length;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Master data"
        title="Programmes & approved intake"
        description="Approved capacity is regulatory master data. Institutions report enrolment against it; they do not edit the approval."
        actions={
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
        }
      />

      <Card className="border-primary/20 bg-primary-soft/30">
        <CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#115e59]">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p>
            This view is read-only for institution users. Approved regular and
            supernumerary allocations are maintained by the regulator. Reported
            enrolment is derived from current student records and corrected
            submissions.
          </p>
        </CardContent>
      </Card>

      {programmes.isLoading ? (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-28" />
            ))}
          </div>
          <Skeleton className="h-96" />
        </div>
      ) : programmes.error ? (
        <EmptyState
          title="Programmes unavailable"
          description={
            programmes.error instanceof ApiError
              ? programmes.error.message
              : "Could not load programmes for this institution."
          }
          icon={<BookOpen className="size-5" />}
          action={
            <Button variant="secondary" onClick={() => programmes.refetch()} icon={<RefreshCw className="size-4" />}>
              Retry
            </Button>
          }
        />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Approved regular" value={approvedRegular.toLocaleString("en-IN")} hint={`${rows.length} active programmes`} />
            <StatCard label="Approved supernumerary" value={approvedSuper.toLocaleString("en-IN")} hint="Separately authorized seats" />
            <StatCard label="Reported enrolment" value={reported.toLocaleString("en-IN")} hint={`Current records in ${year}`} />
            <StatCard
              label="Possible excess"
              value={possibleExcess}
              hint="Programmes needing explanation or correction"
              tone={possibleExcess ? "warning" : "success"}
            />
          </div>
          <ProgrammeTable programmes={rows} />
        </>
      )}
    </div>
  );
}

export default function ProgrammesPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <ProgrammesContent />
    </Suspense>
  );
}
