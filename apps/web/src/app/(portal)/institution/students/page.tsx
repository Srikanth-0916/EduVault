"use client";

import { Filter, RefreshCw, Search, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Suspense, useDeferredValue, useState } from "react";

import { StudentTable } from "@/components/institution/student-table";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useMyProgrammes } from "@/hooks/use-master-data";
import { useStudents } from "@/hooks/use-students";
import { ApiError } from "@/lib/api";

const PAGE_SIZE = 20;

function StudentsContent() {
  const router = useRouter();
  const [year, setYear] = useAcademicYear();
  const [search, setSearch] = useState("");
  const [programmeId, setProgrammeId] = useState("");
  const [enrollmentStatus, setEnrollmentStatus] = useState("");
  const [identityStatus, setIdentityStatus] = useState("");
  const [page, setPage] = useState(1);
  const deferredSearch = useDeferredValue(search);
  const programmes = useMyProgrammes(year);
  const students = useStudents({
    academicYear: year,
    search: deferredSearch || undefined,
    programmeId: programmeId || undefined,
    enrollmentStatus: enrollmentStatus || undefined,
    identityStatus: identityStatus || undefined,
    page,
    pageSize: PAGE_SIZE,
  });
  const total = students.data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function resetPage() {
    setPage(1);
  }

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Student records"
        title="Students"
        description="Search current enrolments, inspect identity state and open corrections. APAAR values are always masked to the last four digits."
        actions={
          <>
            <Select
              aria-label="Academic year"
              value={year}
              onChange={(event) => {
                setYear(event.target.value);
                resetPage();
              }}
              containerClassName="w-36"
            >
              <option value="2025-26">2025-26</option>
              <option value="2026-27">2026-27</option>
              <option value="2027-28">2027-28</option>
            </Select>
            <Button
              size="sm"
              onClick={() => router.push("/institution/students/new")}
              icon={<UserPlus className="size-4" />}
            >
              Add student
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className="space-y-4 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-ink-soft/70">
            <Filter className="size-3.5" aria-hidden="true" /> Filters
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Input
              aria-label="Search by name or student ID"
              placeholder="Search name or student ID"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                resetPage();
              }}
              leading={<Search className="size-4" />}
            />
            <Select
              aria-label="Filter by programme"
              value={programmeId}
              onChange={(event) => {
                setProgrammeId(event.target.value);
                resetPage();
              }}
            >
              <option value="">All programmes</option>
              {(programmes.data ?? []).map((programme) => (
                <option key={programme.id} value={programme.id}>
                  {programme.programmeCode} — {programme.programmeName}
                </option>
              ))}
            </Select>
            <Select
              aria-label="Filter by enrolment status"
              value={enrollmentStatus}
              onChange={(event) => {
                setEnrollmentStatus(event.target.value);
                resetPage();
              }}
            >
              <option value="">All enrolment states</option>
              <option value="ACTIVE">Active</option>
              <option value="PENDING">Pending</option>
              <option value="UNDER_REVIEW">Under review</option>
              <option value="WITHDRAWN">Withdrawn</option>
              <option value="TRANSFERRED">Transferred</option>
              <option value="COMPLETED">Completed</option>
            </Select>
            <Select
              aria-label="Filter by identity status"
              value={identityStatus}
              onChange={(event) => {
                setIdentityStatus(event.target.value);
                resetPage();
              }}
            >
              <option value="">All identity states</option>
              <option value="FORMAT_VALID">Format valid only</option>
              <option value="EXTERNALLY_CONFIRMED">Mock check confirmed</option>
              <option value="EXTERNAL_MISMATCH">Mock check mismatch</option>
              <option value="EXTERNAL_UNAVAILABLE">Mock check unavailable</option>
              <option value="PENDING_EXTERNAL_CHECK">Pending mock check</option>
              <option value="MANUAL_REVIEW">Manual review</option>
              <option value="MISSING">Missing</option>
              <option value="MALFORMED">Malformed</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {students.isLoading ? (
        <Skeleton className="h-96" />
      ) : students.error ? (
        <EmptyState
          title="Students unavailable"
          description={
            students.error instanceof ApiError
              ? students.error.message
              : "Could not load student records."
          }
          action={
            <Button variant="secondary" onClick={() => students.refetch()} icon={<RefreshCw className="size-4" />}>
              Retry
            </Button>
          }
        />
      ) : (
        <>
          <div className="flex items-center justify-between gap-3 text-xs text-ink-soft">
            <p>
              {total.toLocaleString("en-IN")} current record{total === 1 ? "" : "s"} · page {page} of {pageCount}
            </p>
            <p className="hidden sm:block">Last 4 only · mock checks are not live verification</p>
          </div>
          <StudentTable students={students.data?.items ?? []} />
          <div className="flex items-center justify-between gap-3">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= pageCount}
              onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default function StudentsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <StudentsContent />
    </Suspense>
  );
}
