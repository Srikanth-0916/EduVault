"use client";

import { ArrowLeft, Download, FileWarning, RefreshCw, Send, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { AttestationDialog } from "@/components/batches/attestation-dialog";
import { BatchTimeline } from "@/components/batches/batch-timeline";
import { ReceiptDialog } from "@/components/batches/receipt-dialog";
import { RowResultsTable } from "@/components/batches/row-results-table";
import { StatusStepper } from "@/components/batches/status-stepper";
import { ValidationSummary } from "@/components/batches/validation-summary";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useBatch } from "@/hooks/use-batches";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BatchDetail, BatchReceipt, BatchRow } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

function RowEditDialog({
  row,
  open,
  onOpenChange,
  onSave,
  loading,
  error,
}: {
  row: BatchRow | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (values: { studentName: string; studentLocalId: string }) => Promise<void>;
  loading: boolean;
  error: string | null;
}) {
  const [name, setName] = useState(row?.studentName ?? "");
  const [localId, setLocalId] = useState(row?.studentLocalId ?? "");
  const [lastRow, setLastRow] = useState<string | null>(null);
  if (row && row.id !== lastRow) {
    setLastRow(row.id);
    setName(row.studentName ?? "");
    setLocalId(row.studentLocalId ?? "");
  }
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Edit source row ${row?.sourceRowNumber ?? ""}`}
      description="This edit resets the batch to draft and requires a fresh validation run."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button disabled={!name.trim() || !localId.trim()} loading={loading} onClick={() => onSave({ studentName: name.trim(), studentLocalId: localId.trim() })}>Save row</Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Student name" required value={name} onChange={(event) => setName(event.target.value)} />
        <Input label="Institution student ID" required value={localId} onChange={(event) => setLocalId(event.target.value)} />
        <p className="text-xs leading-5 text-ink-soft">APAAR and the remaining CSV fields remain unchanged. Use the source CSV or a future row editor for those fields.</p>
        {error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}
      </div>
    </Dialog>
  );
}

export default function BatchDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const batchQuery = useBatch(params.id);
  const [attestOpen, setAttestOpen] = useState(false);
  const [receiptOpen, setReceiptOpen] = useState(false);
  const [receipt, setReceipt] = useState<BatchReceipt | null>(null);
  const [editRow, setEditRow] = useState<BatchRow | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const isNodal = Boolean(user?.roles.includes("INSTITUTION_NODAL_OFFICER"));
  const canEdit = Boolean(user?.roles.some((role) => ["INSTITUTION_ADMIN", "INSTITUTION_OPERATOR", "INSTITUTION_NODAL_OFFICER"].includes(role)));
  const batch = batchQuery.data;

  const validate = useMutation({
    mutationFn: () => api.post<BatchDetail>(`/submission-batches/${params.id}/validate`, undefined, token),
    onSuccess: (next) => {
      queryClient.setQueryData(["batch", params.id], next);
      void queryClient.invalidateQueries({ queryKey: ["batches"] });
    },
    onError: (error) => setActionError(error instanceof ApiError ? error.message : "Validation failed."),
  });
  const attestAndSubmit = useMutation({
    mutationFn: async (name: string) => {
      await api.post<BatchDetail>(`/submission-batches/${params.id}/attest`, { declaration: true, attestationName: name }, token);
      return api.post<BatchDetail>(`/submission-batches/${params.id}/submit`, undefined, token);
    },
    onSuccess: (next) => {
      setAttestOpen(false);
      queryClient.setQueryData(["batch", params.id], next);
      void queryClient.invalidateQueries({ queryKey: ["batches"] });
      void queryClient.invalidateQueries({ queryKey: ["institution-dashboard"] });
    },
  });
  const edit = useMutation({
    mutationFn: (values: { studentName: string; studentLocalId: string }) =>
      api.patch<BatchDetail>(`/submission-batches/${params.id}/rows/${editRow?.id}`, values, token),
    onSuccess: (next) => {
      setEditRow(null);
      queryClient.setQueryData(["batch", params.id], next);
      void queryClient.invalidateQueries({ queryKey: ["batches"] });
    },
  });

  const errorRows = useMemo(() => batch?.rows.filter((row) => row.rowStatus === "ERROR") ?? [], [batch]);

  async function openReceipt() {
    setActionError(null);
    try {
      const next = await api.get<BatchReceipt>(`/submission-batches/${params.id}/receipt`, token);
      setReceipt(next);
      setReceiptOpen(true);
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : "Could not load the receipt.");
    }
  }

  function downloadErrorCsv() {
    if (!batch || !errorRows.length) return;
    if (!window.confirm("This downloads a student-level error report. The action is auditable. Continue?")) return;
    const header = "row_number,student_local_id,student_name,masked_apaar,rule_id,severity,blocking,message";
    const lines = errorRows.flatMap((row) =>
      row.findings.map((finding) =>
        [row.sourceRowNumber, row.studentLocalId ?? "", row.studentName ?? "", row.maskedApaar, finding.ruleId, finding.severity, finding.blocking, finding.message]
          .map((value) => `"${String(value).replaceAll('"', '""')}"`)
          .join(","),
      ),
    );
    const blob = new Blob([[header, ...lines].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${batch.id}-errors.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (batchQuery.isLoading) return <Skeleton className="h-96" />;
  if (batchQuery.error || !batch) {
    return <EmptyState title="Batch unavailable" description={batchQuery.error instanceof ApiError ? batchQuery.error.message : "The batch could not be loaded."} action={<Button variant="secondary" onClick={() => router.push("/institution/batches")}>Back to batches</Button>} />;
  }

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Submission batch"
        title={batch.fileName ?? batch.id}
        description={`${batch.id} · version ${batch.version} · created ${formatDateTime(batch.createdAt)}`}
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => router.push("/institution/batches")} icon={<ArrowLeft className="size-4" />}>Batches</Button>
            {batch.submittedAt ? <Button variant="secondary" size="sm" onClick={openReceipt} icon={<Download className="size-4" />}>Receipt</Button> : null}
            {batch.status === "VALIDATION_FAILED" && canEdit ? <Button size="sm" onClick={() => validate.mutate()} loading={validate.isPending} icon={<RefreshCw className="size-4" />}>Revalidate</Button> : null}
            {batch.status === "READY_FOR_ATTESTATION" && isNodal ? <Button size="sm" onClick={() => { setActionError(null); setAttestOpen(true); }} icon={<ShieldCheck className="size-4" />}>Attest & submit</Button> : null}
          </>
        }
      />

      {actionError ? <p role="alert" className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{actionError}</p> : null}
      {batch.decision ? <div className={`rounded-[10px] border p-4 ${batch.decision === "ACCEPT" ? "border-success/30 bg-success-soft/35" : batch.decision === "RETURN" ? "border-accent/30 bg-accent-soft/40" : "border-danger/30 bg-danger-soft/35"}`}><p className="text-sm font-semibold text-ink">AICTE decision: {batch.decision}</p><p className="mt-1 text-xs leading-5 text-ink-soft">{batch.decisionReason ?? "No reason supplied."}</p></div> : null}

      <Card>
        <CardContent className="p-5"><StatusStepper status={batch.status} /></CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <ValidationSummary summary={batch.validationSummary ?? batch.summary} />
        <Card>
          <CardHeader><CardTitle>Batch provenance</CardTitle><CardDescription>File identity and workflow timestamps.</CardDescription></CardHeader>
          <CardContent className="space-y-3 pt-3">
            <dl className="space-y-2 text-xs">
              <div className="flex justify-between gap-3"><dt className="text-ink-soft">File</dt><dd className="text-right font-medium text-ink">{batch.fileName ?? "—"}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-soft">Checksum</dt><dd className="max-w-[65%] break-all text-right font-mono text-[10px] text-ink">{batch.fileChecksum ?? "—"}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-soft">Rows</dt><dd className="tabular text-ink">{batch.rowCount ?? 0}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-soft">Status</dt><dd><StatusBadge family="batch" status={batch.status} /></dd></div>
            </dl>
            <BatchTimeline batch={batch} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-start justify-between gap-3"><div><CardTitle>Row results</CardTitle><CardDescription>Every error remains actionable; warnings are visible rather than hidden in a toast.</CardDescription></div>{errorRows.length ? <Button variant="secondary" size="sm" onClick={downloadErrorCsv} icon={<Download className="size-3.5" />}>Download error CSV</Button> : null}</CardHeader>
        <CardContent className="pt-3"><RowResultsTable batch={batch} canEdit={canEdit} onEdit={async (row) => setEditRow(row)} /></CardContent>
      </Card>

      {batch.status === "READY_FOR_ATTESTATION" && !isNodal ? <p className="rounded-[8px] border border-accent/25 bg-accent-soft/35 px-3 py-2.5 text-xs leading-5 text-[#92400e]">This batch is ready, but only an institution nodal officer can record the attestation and submit it.</p> : null}
      {batch.status === "RETURNED_FOR_CORRECTION" ? <p className="rounded-[8px] border border-accent/25 bg-accent-soft/35 px-3 py-2.5 text-xs leading-5 text-[#92400e]">This batch was returned. Edit the affected rows, revalidate, attest again and resubmit as a new version.</p> : null}

      <AttestationDialog batch={batch} open={attestOpen} onOpenChange={setAttestOpen} loading={attestAndSubmit.isPending} error={attestAndSubmit.error instanceof ApiError ? attestAndSubmit.error.message : null} onAttest={async (name) => { await attestAndSubmit.mutateAsync(name); }} />
      <ReceiptDialog receipt={receipt} open={receiptOpen} onOpenChange={setReceiptOpen} />
      <RowEditDialog row={editRow} open={Boolean(editRow)} onOpenChange={(open) => !open && setEditRow(null)} onSave={async (values) => { await edit.mutateAsync(values); }} loading={edit.isPending} error={edit.error instanceof ApiError ? edit.error.message : null} />
    </div>
  );
}
