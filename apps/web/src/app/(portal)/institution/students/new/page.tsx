"use client";

import { ArrowLeft, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { StudentForm, type StudentFormPayload } from "@/components/institution/student-form";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useMyProgrammes } from "@/hooks/use-master-data";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EnrollmentDetail } from "@/lib/types";

function NewStudentContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token } = useAuth();
  const [year, setYear] = useAcademicYear();
  const programmes = useMyProgrammes(year);
  const [apiError, setApiError] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: (payload: StudentFormPayload) =>
      api.post<EnrollmentDetail>("/enrollments", payload, token),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["students"] });
      void queryClient.invalidateQueries({ queryKey: ["institution-dashboard"] });
      router.push(`/institution/students/${created.id}`);
    },
    onError: (error) => {
      setApiError(
        error instanceof ApiError ? error.message : "Could not create the enrolment.",
      );
    },
  });

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Student records"
        title="Add a synthetic student"
        description="Create a versioned enrolment record. APAAR is optional, write-only and never returned in full."
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
              onClick={() => router.push("/institution/students")}
              icon={<ArrowLeft className="size-4" />}
            >
              Back to students
            </Button>
          </>
        }
      />
      {programmes.isLoading ? (
        <Skeleton className="h-96" />
      ) : programmes.error ? (
        <EmptyState
          title="Programmes unavailable"
          description={
            programmes.error instanceof ApiError
              ? programmes.error.message
              : "Programmes are required before a student can be created."
          }
          action={
            <Button variant="secondary" onClick={() => programmes.refetch()} icon={<RefreshCw className="size-4" />}>
              Retry
            </Button>
          }
        />
      ) : !(programmes.data ?? []).length ? (
        <EmptyState
          title="No programmes configured"
          description="An institution administrator or AICTE supervisor must configure a programme first."
        />
      ) : (
        <div className="max-w-4xl">
          <StudentForm
            programmes={programmes.data ?? []}
            academicYear={year}
            submitting={mutation.isPending}
            apiError={apiError}
            onSubmit={async (payload) => {
              setApiError(null);
              await mutation.mutateAsync(payload);
            }}
          />
        </div>
      )}
    </div>
  );
}

export default function NewStudentPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <NewStudentContent />
    </Suspense>
  );
}
