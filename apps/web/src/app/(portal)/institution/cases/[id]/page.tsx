"use client";

import { ArrowLeft, MessageSquare, RefreshCw, Send } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CaseEvidence } from "@/components/cases/case-evidence";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input, Textarea } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCase } from "@/hooks/use-cases";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { titleCase } from "@/lib/utils";

export default function InstitutionCaseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const caseQuery = useCase(params.id);
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const isStaff = Boolean(user?.roles.some((role) => ["INSTITUTION_ADMIN", "INSTITUTION_OPERATOR", "INSTITUTION_NODAL_OFFICER"].includes(role)));
  const respond = useMutation({
    mutationFn: () => api.post(`/duplicate-cases/${params.id}/respond`, { message: message.trim() }, token),
    onSuccess: () => {
      setMessage("");
      void queryClient.invalidateQueries({ queryKey: ["case", params.id] });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not send the response."),
  });
  const caseItem = caseQuery.data;

  if (caseQuery.isLoading) return <Skeleton className="h-96" />;
  if (caseQuery.error || !caseItem) return <EmptyState title="Case unavailable" description={caseQuery.error instanceof ApiError ? caseQuery.error.message : "The case could not be loaded."} action={<Button variant="secondary" onClick={() => router.push("/institution/cases")}>Back to cases</Button>} />;

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Review case" title={titleCase(caseItem.matchType)} description={`${caseItem.id} · discovered in ${caseItem.discoveredBatchId ?? "manual review"}`} actions={<Button variant="secondary" size="sm" onClick={() => router.push("/institution/cases")} icon={<ArrowLeft className="size-4" />}>Cases</Button>} />
      <div className="flex flex-wrap items-center gap-2"><StatusBadge family="severity" status={caseItem.severity} /><StatusBadge family="case" status={caseItem.status} /><span className="text-xs text-ink-soft">Opened {new Date(caseItem.openedAt).toLocaleString("en-IN")}</span></div>
      <CaseEvidence caseItem={caseItem} />
      {isStaff && caseItem.status !== "RESOLVED" ? <Card><CardHeader><CardTitle className="flex items-center gap-2"><MessageSquare className="size-4 text-primary" aria-hidden="true" />Respond to reviewer</CardTitle></CardHeader><CardContent className="space-y-4 pt-3"><Textarea label="Response" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Provide transfer, correction or concurrent-enrolment context…" hint="The response is recorded in the case evidence and visible to AICTE reviewers." />{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}<div className="flex justify-end"><Button disabled={message.trim().length < 3} loading={respond.isPending} onClick={() => { setError(null); respond.mutate(); }} icon={<Send className="size-4" />}>Send response</Button></div></CardContent></Card> : null}
      {caseItem.status === "RESOLVED" ? <p className="rounded-[8px] border border-success/25 bg-success-soft/35 px-3 py-2.5 text-xs text-success">This case is resolved. Its evidence and resolution reason remain available for audit.</p> : null}
      {caseQuery.isFetching ? <p className="flex items-center gap-1.5 text-xs text-ink-soft"><RefreshCw className="size-3 animate-spin" />Refreshing case…</p> : null}
    </div>
  );
}
