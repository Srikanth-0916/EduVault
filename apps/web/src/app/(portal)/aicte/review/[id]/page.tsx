"use client";

import { ArrowLeft, RefreshCw } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { BatchDecisionPanel } from "@/components/aicte/batch-decision-panel";
import { BatchTimeline } from "@/components/batches/batch-timeline";
import { RowResultsTable } from "@/components/batches/row-results-table";
import { StatusStepper } from "@/components/batches/status-stepper";
import { ValidationSummary } from "@/components/batches/validation-summary";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useBatch } from "@/hooks/use-batches";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BatchDetail } from "@/lib/types";

export default function ReviewBatchPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const batch = useBatch(params.id);
  const [error, setError] = useState<string | null>(null);
  const decide = useMutation({
    mutationFn: ({ decision, reasonCode, reason }: { decision: "ACCEPT" | "RETURN" | "REJECT"; reasonCode: string; reason: string }) => api.post<BatchDetail>(`/submission-batches/${params.id}/decision`, { decision, reasonCode, reason }, token),
    onSuccess: (next) => { queryClient.setQueryData(["batch", params.id], next); void queryClient.invalidateQueries({ queryKey: ["review-queue"] }); void queryClient.invalidateQueries({ queryKey: ["review-summary"] }); },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not record the decision."),
  });
  const data = batch.data;
  if (batch.isLoading) return <Skeleton className="h-96" />;
  if (batch.error || !data) return <EmptyState title="Review batch unavailable" description={batch.error instanceof ApiError ? batch.error.message : "The batch could not be loaded."} action={<Button variant="secondary" onClick={() => router.push("/aicte/review")}>Back to review</Button>} />;
  return <div className="space-y-5">
    <PageHeader eyebrow="AICTE review workspace" title={data.fileName ?? data.id} description={`${data.id} · institution ${data.institutionId} · version ${data.version}`} actions={<Button variant="secondary" size="sm" onClick={() => router.push("/aicte/review")} icon={<ArrowLeft className="size-4" />}>Review queue</Button>} />
    {error ? <p role="alert" className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p> : null}
    <Card><CardContent className="p-5"><StatusStepper status={data.status} /></CardContent></Card>
    <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]"><ValidationSummary summary={data.validationSummary ?? data.summary} /><Card><CardHeader><CardTitle>Review timeline</CardTitle><CardDescription>State changes and submitted version.</CardDescription></CardHeader><CardContent className="pt-3"><BatchTimeline batch={data} /></CardContent></Card></div>
    <Card><CardHeader><CardTitle>Validation evidence</CardTitle><CardDescription>Findings are rule-based; APAAR values remain masked and external results are mock-labelled.</CardDescription></CardHeader><CardContent className="pt-3"><RowResultsTable batch={data} canEdit={false} onEdit={async () => undefined} /></CardContent></Card>
    <BatchDecisionPanel batch={data} role={user?.primaryRole ?? ""} loading={decide.isPending} error={decide.error instanceof ApiError ? decide.error.message : null} onDecision={async (decision, reasonCode, reason) => { setError(null); await decide.mutateAsync({ decision, reasonCode, reason }); }} />
    {batch.isFetching ? <p className="flex items-center gap-1.5 text-xs text-ink-soft"><RefreshCw className="size-3 animate-spin" />Refreshing review evidence…</p> : null}
  </div>;
}
