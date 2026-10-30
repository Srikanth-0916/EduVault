"use client";

import { ArrowLeft, CheckCircle2, FileCheck2, Loader2, UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { Suspense, useState } from "react";

import { FileDropzone } from "@/components/batches/file-dropzone";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useMyInstitution, useMyProgrammes } from "@/hooks/use-master-data";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BatchDetail } from "@/lib/types";

const BUNDLED_SAMPLE = [
  "institution_student_id,apaar_id,student_name,programme_code,campus_code,academic_year,admission_date,exit_date,enrollment_status,seat_classification,admission_category,nri_status,oci_status,foreign_national_status,approval_reference,date_of_birth,gender",
  "DEMO2026001,910000000101,Synthetic Sample One,CSE,AIT-MAIN,2026-27,2026-07-15,,ACTIVE,APPROVED_REGULAR,GENERAL,NO,NO,NO,,2007-04-18,FEMALE",
  "DEMO2026002,910000000102,Synthetic Sample Two,ECE,AIT-MAIN,2026-27,2026-07-15,,ACTIVE,APPROVED_REGULAR,GENERAL,NO,NO,NO,,2007-05-20,MALE",
  "DEMO2026003,910000000103,Synthetic Sample Three,ECE,AIT-MAIN,2026-27,2026-07-15,,ACTIVE,APPROVED_SUPERNUMERARY,GENERAL,NO,NO,NO,DEMO/SN/2026,,FEMALE",
].join("\n");

function NewBatchContent() {
  const router = useRouter();
  const { token } = useAuth();
  const [year, setYear] = useAcademicYear();
  const institution = useMyInstitution(year);
  const programmes = useMyProgrammes(year);
  const [file, setFile] = useState<File | null>(null);
  const [campusId, setCampusId] = useState("");
  const [programmeId, setProgrammeId] = useState("");
  const [step, setStep] = useState<"select" | "upload" | "validate" | "done">("select");
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const campuses = institution.data?.campuses ?? [];

  async function createAndUpload(selectedFile: File) {
    setBusy(true);
    setError(null);
    try {
      const created = await api.post<BatchDetail>(
        "/submission-batches",
        { academicYear: year, campusId: campusId || null, programmeId: programmeId || null, sourceType: "CSV_UPLOAD" },
        token,
      );
      const form = new FormData();
      form.append("file", selectedFile, selectedFile.name);
      const uploaded = await api.upload<BatchDetail>(`/submission-batches/${created.id}/file`, form, token);
      setBatch(uploaded);
      setStep("validate");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not upload this batch.");
    } finally {
      setBusy(false);
    }
  }

  async function useBundledSample() {
    const selected = new File([BUNDLED_SAMPLE], "bundled-synthetic-sample.csv", { type: "text/csv" });
    setFile(selected);
    await createAndUpload(selected);
  }

  async function validate() {
    if (!batch) return;
    setBusy(true);
    setError(null);
    try {
      const validated = await api.post<BatchDetail>(`/submission-batches/${batch.id}/validate`, undefined, token);
      setBatch(validated);
      setStep("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Validation could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Submission workflow"
        title="Create a batch"
        description="Keep the batch ID through upload and validation so the full checksum and rule-result trail remains linked."
        actions={<Button variant="secondary" size="sm" onClick={() => router.push("/institution/batches")} icon={<ArrowLeft className="size-4" />}>Back to batches</Button>}
      />

      <ol className="grid gap-2 sm:grid-cols-4" aria-label="New batch steps">
        {["Select year", "Upload CSV", "Validate", "Review results"].map((label, index) => {
          const active = index === ({ select: 0, upload: 1, validate: 2, done: 3 }[step]);
          const complete = index < ({ select: 0, upload: 1, validate: 2, done: 3 }[step]);
          return <li key={label} className={`rounded-[8px] border px-3 py-2 text-xs ${active ? "border-primary bg-primary-soft text-primary" : complete ? "border-success/30 bg-success-soft/40 text-success" : "border-border bg-surface text-ink-soft/60"}`}><span className="font-semibold">{index + 1}.</span> {label}</li>;
        })}
      </ol>

      {error ? <p role="alert" className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p> : null}

      {step === "select" ? (
        <Card className="max-w-3xl">
          <CardHeader><CardTitle>1. Select scope</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Select label="Academic year" value={year} onChange={(event) => setYear(event.target.value)}>
              <option value="2025-26">2025-26</option><option value="2026-27">2026-27</option><option value="2027-28">2027-28</option>
            </Select>
            <Select label="Campus (optional)" value={campusId} onChange={(event) => setCampusId(event.target.value)}>
              <option value="">All campuses</option>{campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
            </Select>
            <Select label="Programme (optional)" value={programmeId} onChange={(event) => setProgrammeId(event.target.value)}>
              <option value="">All programmes</option>{(programmes.data ?? []).map((programme) => <option key={programme.id} value={programme.id}>{programme.programmeCode} — {programme.programmeName}</option>)}
            </Select>
            <Input label="Source" value="CSV upload" readOnly className="bg-surface-muted" />
            <div className="sm:col-span-2 flex items-center justify-between gap-3 border-t border-border pt-4">
              <p className="text-xs leading-5 text-ink-soft">The scope is a filter and does not replace row-level programme and campus validation.</p>
              <Button onClick={() => setStep("upload")} icon={<UploadCloud className="size-4" />}>Continue to upload</Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {step === "upload" ? (
        <Card className="max-w-3xl">
          <CardHeader><CardTitle>2. Upload CSV</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <FileDropzone fileName={file?.name} onFile={setFile} disabled={busy} />
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <Button variant="secondary" onClick={() => setStep("select")}>Back</Button>
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" onClick={useBundledSample} loading={busy} icon={<FileCheck2 className="size-4" />}>Use bundled sample</Button>
                <Button disabled={!file} onClick={() => file && createAndUpload(file)} loading={busy}>Upload and stage</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {step === "validate" && batch ? (
        <Card className="max-w-3xl">
          <CardHeader><CardTitle>3. Run validation</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3 rounded-[10px] border border-border bg-surface-muted/35 p-4">
              <CheckCircle2 className="mt-0.5 size-5 text-primary" aria-hidden="true" />
              <div><p className="text-sm font-medium text-ink">{batch.fileName} staged</p><p className="mt-1 text-xs leading-5 text-ink-soft">{batch.rowCount} rows · checksum {batch.fileChecksum?.slice(0, 16)}…</p></div>
            </div>
            <p className="text-sm leading-6 text-ink-soft">Validation checks APAAR format separately from mock external status, duplicate cases, programme mapping, dates, supernumerary references and capacity warnings.</p>
            <div className="flex justify-end gap-2 border-t border-border pt-4"><Button variant="secondary" onClick={() => setStep("upload")}>Back</Button><Button onClick={validate} loading={busy} icon={busy ? <Loader2 className="size-4" /> : <CheckCircle2 className="size-4" />}>Run validation</Button></div>
          </CardContent>
        </Card>
      ) : null}

      {step === "done" && batch ? (
        <Card className="max-w-3xl border-success/25">
          <CardContent className="space-y-4 p-5">
            <div className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 size-5 text-success" aria-hidden="true" /><div><p className="font-medium text-ink">Validation complete</p><p className="mt-1 text-sm text-ink-soft">The row-level findings and batch summary are ready for review.</p></div><StatusBadge family="batch" status={batch.status} /></div>
            <div className="flex justify-end"><Button onClick={() => router.push(`/institution/batches/${batch.id}`)}>Open batch results</Button></div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

export default function NewBatchPage() {
  return <Suspense fallback={<div className="flex min-h-[30vh] items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div>}><NewBatchContent /></Suspense>;
}
