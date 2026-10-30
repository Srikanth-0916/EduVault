"use client";

import {
  ArrowLeft,
  BadgeCheck,
  Clock3,
  FlaskConical,
  PencilLine,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EnrollmentTimeline } from "@/components/institution/enrollment-timeline";
import { IdentityStatus } from "@/components/institution/identity-status";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useStudent } from "@/hooks/use-students";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EnrollmentDetail, IdentityVerification } from "@/lib/types";
import { formatDate, formatDateTime, titleCase } from "@/lib/utils";

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border/70 py-2.5 last:border-0">
      <dt className="text-xs text-ink-soft/75">{label}</dt>
      <dd className="text-right text-xs font-medium text-ink">{value}</dd>
    </div>
  );
}

function VerificationRow({ item }: { item: IdentityVerification }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5">
      <div>
        <p className="text-xs font-medium text-ink">{titleCase(item.result)}</p>
        <p className="mt-0.5 text-[11px] text-ink-soft/70">
          {item.provider} · {formatDateTime(item.checkedAt)}
        </p>
        <p className="mt-0.5 text-[11px] text-ink-soft/70">{item.purpose ?? "Identity check"}</p>
      </div>
      <Badge tone={item.isMock ? "mock" : "neutral"}>
        <FlaskConical className="size-3" aria-hidden="true" /> Mock
      </Badge>
    </div>
  );
}

function CorrectionDialog({
  open,
  onOpenChange,
  student,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  student: EnrollmentDetail;
  onSaved: (next: EnrollmentDetail) => void;
}) {
  const { token } = useAuth();
  const [name, setName] = useState(student.studentFullName);
  const [status, setStatus] = useState(student.enrollmentStatus);
  const [seat, setSeat] = useState(student.seatClassification);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: () =>
      api.patch<EnrollmentDetail>(
        `/enrollments/${student.id}`,
        {
          studentFullName: name,
          enrollmentStatus: status,
          seatClassification: seat,
          reason,
        },
        token,
      ),
    onSuccess: (next) => {
      onOpenChange(false);
      onSaved(next);
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : "Could not save the correction."),
  });

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Correct enrolment"
      description="A correction creates a new current version. The previous snapshot remains in history and is never overwritten."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            loading={mutation.isPending}
            disabled={reason.trim().length < 3}
            onClick={() => {
              setError(null);
              mutation.mutate();
            }}
          >
            Save correction
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Full name" value={name} onChange={(event) => setName(event.target.value)} />
        <Select label="Enrolment status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
          <option value="UNDER_REVIEW">Under review</option>
          <option value="WITHDRAWN">Withdrawn</option>
          <option value="TRANSFERRED">Transferred</option>
          <option value="COMPLETED">Completed</option>
        </Select>
        <Select label="Seat classification" value={seat} onChange={(event) => setSeat(event.target.value)}>
          <option value="APPROVED_REGULAR">Approved regular</option>
          <option value="APPROVED_SUPERNUMERARY">Approved supernumerary</option>
          <option value="OTHER">Other</option>
        </Select>
        <Input
          label="Reason for correction"
          required
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          hint="Recorded in the version snapshot and audit trail."
        />
        {error ? <p className="text-sm text-danger">{error}</p> : null}
      </div>
    </Dialog>
  );
}

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const student = useStudent(params.id);
  const [correctionOpen, setCorrectionOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const verify = useMutation({
    mutationFn: () =>
      api.post<{ identityStatus: string; verification: IdentityVerification }>(
        `/enrollments/${params.id}/verify-identity`,
        undefined,
        token,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["student", params.id] });
      void queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (error) =>
      setActionError(
        error instanceof ApiError ? error.message : "Could not run the mock identity check.",
      ),
  });
  const canEdit = Boolean(
    user?.roles.some((role) =>
      ["INSTITUTION_ADMIN", "INSTITUTION_OPERATOR", "INSTITUTION_NODAL_OFFICER"].includes(role),
    ),
  );

  if (student.isLoading) return <Skeleton className="h-96" />;
  if (student.error || !student.data) {
    return (
      <div className="space-y-4">
        <PageHeader eyebrow="Student record" title="Record unavailable" />
        <EmptyState
          title="Could not load this enrolment"
          description={
            student.error instanceof ApiError
              ? student.error.message
              : "The record may not exist or may be outside your access scope."
          }
          action={
            <Button variant="secondary" onClick={() => router.push("/institution/students")}>
              Back to students
            </Button>
          }
        />
      </div>
    );
  }
  const data = student.data;
  const latestVerification = data.verifications[0];

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Student record"
        title={data.studentFullName}
        description={`${data.studentLocalId} · ${data.programmeName ?? "Programme"} · ${data.academicYear}`}
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => router.push("/institution/students")}
              icon={<ArrowLeft className="size-4" />}
            >
              Students
            </Button>
            {canEdit ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCorrectionOpen(true)}
                  icon={<PencilLine className="size-4" />}
                >
                  Correct
                </Button>
                <Button
                  size="sm"
                  loading={verify.isPending}
                  onClick={() => {
                    setActionError(null);
                    verify.mutate();
                  }}
                  icon={<ShieldCheck className="size-4" />}
                >
                  Run mock check
                </Button>
              </>
            ) : null}
          </>
        }
      />

      {actionError ? (
        <p role="alert" className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">
          {actionError}
        </p>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Enrolment summary</CardTitle>
              <CardDescription>
                Current version {data.version} · {data.isCurrent ? "current record" : "historical snapshot"}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-3">
              <dl className="grid gap-x-8 sm:grid-cols-2">
                <DetailRow label="Programme" value={data.programmeName ?? "—"} />
                <DetailRow label="Campus" value={data.campusName ?? "—"} />
                <DetailRow label="Academic year" value={data.academicYear} />
                <DetailRow label="Admission date" value={formatDate(data.admissionDate)} />
                <DetailRow label="Exit date" value={formatDate(data.exitDate)} />
                <DetailRow label="Enrolment status" value={<StatusBadge family="enrollment" status={data.enrollmentStatus} />} />
                <DetailRow label="Seat classification" value={titleCase(data.seatClassification)} />
                <DetailRow label="Admission category" value={data.admissionCategory ?? "—"} />
                <DetailRow label="Supernumerary reference" value={data.supernumeraryApprovalReference ?? "—"} />
                <DetailRow
                  label="AICTE acceptance"
                  value={
                    data.recordAcceptedAt ? (
                      <Badge tone="success">
                        <BadgeCheck className="size-3" aria-hidden="true" /> Accepted {formatDate(data.recordAcceptedAt)}
                      </Badge>
                    ) : (
                      <Badge tone="neutral">Not accepted</Badge>
                    )
                  }
                />
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Identity</CardTitle>
              <CardDescription>
                Three separate signals: format validity, mock external check, and AICTE acceptance.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-3">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-border bg-surface-muted/35 p-4">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">APAAR display</p>
                  <p className="mt-1 font-mono text-lg text-ink">{data.maskedApaar}</p>
                  <p className="mt-1 text-[11px] text-ink-soft/70">Last 4 only. The full value is never returned.</p>
                </div>
                <IdentityStatus
                  status={data.identityStatus ?? "MISSING"}
                  verifiedAt={latestVerification ? formatDateTime(latestVerification.checkedAt) : null}
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[8px] border border-border p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">Format</p>
                  <p className="mt-1 text-xs text-ink">
                    {data.identityStatus === "MALFORMED" || data.identityStatus === "MISSING"
                      ? "Invalid format or missing"
                      : "Format valid"}
                  </p>
                </div>
                <div className="rounded-[8px] border border-border p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">External check</p>
                  <p className="mt-1 text-xs text-ink">
                    {latestVerification ? `${titleCase(latestVerification.result)} (mock)` : "Not run"}
                  </p>
                </div>
                <div className="rounded-[8px] border border-border p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/70">AICTE acceptance</p>
                  <p className="mt-1 text-xs text-ink">{data.recordAcceptedAt ? "Accepted" : "Not accepted"}</p>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.07em] text-ink-soft/70">Mock check history</p>
                {data.verifications.length ? (
                  data.verifications.map((item) => <VerificationRow key={item.id} item={item} />)
                ) : (
                  <p className="rounded-[8px] border border-dashed border-border px-3 py-4 text-xs text-ink-soft">
                    No external check has been requested. Format validity alone is not verification.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {data.findings.length ? (
            <Card>
              <CardHeader>
                <CardTitle>Submission findings</CardTitle>
                <CardDescription>Evidence from the batch that produced this record.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 pt-3">
                {data.findings.map((finding) => (
                  <div key={finding.id} className="flex items-start justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5">
                    <div>
                      <p className="text-xs font-medium text-ink">{finding.message}</p>
                      <p className="mt-0.5 text-[11px] text-ink-soft/70">
                        {finding.ruleId} · {finding.code} · {finding.field ?? "record"}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <StatusBadge family="severity" status={finding.severity} />
                      {finding.blocking ? <Badge tone="danger">Blocking</Badge> : <Badge tone="neutral">Advisory</Badge>}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Attributes</CardTitle>
              <CardDescription>Declared values are tri-state; blank never means No.</CardDescription>
            </CardHeader>
            <CardContent className="pt-3">
              <dl>
                <DetailRow label="NRI" value={titleCase(data.nriStatus)} />
                <DetailRow label="OCI" value={titleCase(data.ociStatus)} />
                <DetailRow label="Foreign national" value={titleCase(data.foreignNationalStatus)} />
                <DetailRow label="Last updated" value={formatDateTime(data.updatedAt)} />
              </dl>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Version history</CardTitle>
              <CardDescription>Corrections are append-only snapshots.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <EnrollmentTimeline versions={data.versions} />
            </CardContent>
          </Card>
          <Card className="border-dashed">
            <CardContent className="flex items-start gap-2 p-4 text-[11px] leading-5 text-ink-soft">
              <Clock3 className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
              <p>
                This prototype stores synthetic records only. Mock external checks are
                deterministic test responses, not government verification.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      <CorrectionDialog
        open={correctionOpen}
        onOpenChange={setCorrectionOpen}
        student={data}
        onSaved={(next) => {
          void queryClient.invalidateQueries({ queryKey: ["students"] });
          void queryClient.invalidateQueries({ queryKey: ["student", params.id] });
          router.replace(`/institution/students/${next.id}`);
        }}
      />
    </div>
  );
}
