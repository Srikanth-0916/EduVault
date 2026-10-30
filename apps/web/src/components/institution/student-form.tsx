"use client";

import { AlertTriangle, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Programme } from "@/lib/types";

export interface StudentFormPayload {
  studentLocalId: string;
  studentFullName: string;
  apaarId: string | null;
  programmeId: string;
  campusId: string | null;
  academicYear: string;
  admissionDate: string;
  exitDate: string | null;
  enrollmentStatus: string;
  seatClassification: string;
  admissionCategory: string | null;
  nriStatus: string;
  ociStatus: string;
  foreignNationalStatus: string;
  supernumeraryApprovalReference: string | null;
}

const EMPTY = {
  studentLocalId: "",
  studentFullName: "",
  apaarId: "",
  programmeId: "",
  academicYear: "2026-27",
  admissionDate: "2026-08-01",
  exitDate: "",
  enrollmentStatus: "PENDING",
  seatClassification: "APPROVED_REGULAR",
  admissionCategory: "GENERAL",
  nriStatus: "UNKNOWN",
  ociStatus: "UNKNOWN",
  foreignNationalStatus: "UNKNOWN",
  supernumeraryApprovalReference: "",
  notes: "",
};

export function StudentForm({
  programmes,
  academicYear,
  submitting,
  apiError,
  onSubmit,
}: {
  programmes: Programme[];
  academicYear: string;
  submitting: boolean;
  apiError: string | null;
  onSubmit: (payload: StudentFormPayload) => Promise<void>;
}) {
  const [form, setForm] = useState({ ...EMPTY, academicYear });
  const [error, setError] = useState<string | null>(null);
  const programme = programmes.find((item) => item.id === form.programmeId);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!form.studentLocalId.trim() || !form.studentFullName.trim()) {
      setError("Institution student ID and full name are required.");
      return;
    }
    if (!form.programmeId) {
      setError("Select a programme.");
      return;
    }
    if (form.apaarId && !/^\d{12}$/.test(form.apaarId.trim())) {
      setError("APAAR must be exactly 12 digits, or left blank.");
      return;
    }
    if (form.exitDate && form.exitDate < form.admissionDate) {
      setError("Exit date must not be before admission date.");
      return;
    }
    if (
      form.seatClassification === "APPROVED_SUPERNUMERARY" &&
      !form.supernumeraryApprovalReference.trim()
    ) {
      setError("A supernumerary approval reference is required for this seat classification.");
      return;
    }
    await onSubmit({
      studentLocalId: form.studentLocalId.trim(),
      studentFullName: form.studentFullName.trim(),
      apaarId: form.apaarId.trim() || null,
      programmeId: form.programmeId,
      campusId: programme?.campusId ?? null,
      academicYear: form.academicYear,
      admissionDate: form.admissionDate,
      exitDate: form.exitDate || null,
      enrollmentStatus: form.enrollmentStatus,
      seatClassification: form.seatClassification,
      admissionCategory: form.admissionCategory || null,
      nriStatus: form.nriStatus,
      ociStatus: form.ociStatus,
      foreignNationalStatus: form.foreignNationalStatus,
      supernumeraryApprovalReference:
        form.supernumeraryApprovalReference.trim() || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      <Card className="border-accent/30 bg-accent-soft/35">
        <CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#92400e]">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p>
            Synthetic demo record only. Do not enter real student data. The APAAR
            value is write-only, encrypted at rest, and displayed masked to the
            last four digits.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Input
          label="Institution student ID"
          required
          value={form.studentLocalId}
          onChange={(event) => update("studentLocalId", event.target.value)}
          placeholder="AIT2026CSE001"
          autoComplete="off"
        />
        <Input
          label="Full name"
          required
          value={form.studentFullName}
          onChange={(event) => update("studentFullName", event.target.value)}
          placeholder="Synthetic Student"
          autoComplete="off"
        />
        <Input
          label="APAAR ID"
          value={form.apaarId}
          onChange={(event) => update("apaarId", event.target.value)}
          hint="Optional in this prototype. Twelve digits exactly; only the last four are returned."
          inputMode="numeric"
          maxLength={12}
          autoComplete="off"
        />
        <Select
          label="Programme"
          required
          value={form.programmeId}
          onChange={(event) => update("programmeId", event.target.value)}
        >
          <option value="">Select a programme</option>
          {programmes.map((item) => (
            <option key={item.id} value={item.id}>
              {item.programmeCode} — {item.programmeName}
            </option>
          ))}
        </Select>
        <Input
          label="Campus"
          value={programme?.campusName ?? "Select a programme first"}
          readOnly
          className="bg-surface-muted"
        />
        <Select
          label="Academic year"
          value={form.academicYear}
          onChange={(event) => update("academicYear", event.target.value)}
        >
          <option value="2025-26">2025-26</option>
          <option value="2026-27">2026-27</option>
          <option value="2027-28">2027-28</option>
        </Select>
        <Input
          label="Admission date"
          type="date"
          required
          value={form.admissionDate}
          onChange={(event) => update("admissionDate", event.target.value)}
        />
        <Input
          label="Exit date"
          type="date"
          value={form.exitDate}
          onChange={(event) => update("exitDate", event.target.value)}
          hint="Leave blank for a continuing student."
        />
        <Select
          label="Enrolment status"
          value={form.enrollmentStatus}
          onChange={(event) => update("enrollmentStatus", event.target.value)}
        >
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
          <option value="UNDER_REVIEW">Under review</option>
          <option value="WITHDRAWN">Withdrawn</option>
          <option value="TRANSFERRED">Transferred</option>
          <option value="COMPLETED">Completed</option>
        </Select>
        <Select
          label="Seat classification"
          value={form.seatClassification}
          onChange={(event) => update("seatClassification", event.target.value)}
        >
          <option value="APPROVED_REGULAR">Approved regular</option>
          <option value="APPROVED_SUPERNUMERARY">Approved supernumerary</option>
          <option value="OTHER">Other</option>
        </Select>
        <Input
          label="Admission category"
          value={form.admissionCategory}
          onChange={(event) => update("admissionCategory", event.target.value)}
          placeholder="GENERAL"
        />
        <Input
          label="Supernumerary approval reference"
          value={form.supernumeraryApprovalReference}
          onChange={(event) => update("supernumeraryApprovalReference", event.target.value)}
          disabled={form.seatClassification !== "APPROVED_SUPERNUMERARY"}
          hint="Required only for approved supernumerary seats."
        />
        <Select
          label="NRI status"
          value={form.nriStatus}
          onChange={(event) => update("nriStatus", event.target.value)}
        >
          <option value="UNKNOWN">Unknown</option>
          <option value="NO">No</option>
          <option value="YES">Yes</option>
        </Select>
        <Select
          label="OCI status"
          value={form.ociStatus}
          onChange={(event) => update("ociStatus", event.target.value)}
        >
          <option value="UNKNOWN">Unknown</option>
          <option value="NO">No</option>
          <option value="YES">Yes</option>
        </Select>
        <Select
          label="Foreign national status"
          value={form.foreignNationalStatus}
          onChange={(event) => update("foreignNationalStatus", event.target.value)}
        >
          <option value="UNKNOWN">Unknown</option>
          <option value="NO">No</option>
          <option value="YES">Yes</option>
        </Select>
      </div>

      <Textarea
        label="Internal note"
        value={form.notes}
        onChange={(event) => update("notes", event.target.value)}
        hint="Not stored by this prototype form; use the audit trail for governance notes."
      />

      {error || apiError ? (
        <p
          role="alert"
          className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger"
        >
          {error ?? apiError}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" loading={submitting} icon={<ShieldCheck className="size-4" />}>
          Create synthetic enrolment
        </Button>
        <p className="text-xs text-ink-soft/75">
          The record is created by the API with a version snapshot and an audit event.
        </p>
      </div>
    </form>
  );
}
