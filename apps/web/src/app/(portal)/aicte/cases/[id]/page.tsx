"use client";

import { ArrowLeft, MessageSquare, ShieldCheck } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CaseEvidence } from "@/components/cases/case-evidence";
import { ResolutionDialog } from "@/components/cases/resolution-dialog";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Textarea } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCase } from "@/hooks/use-cases";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime, titleCase } from "@/lib/utils";

export default function AicteCaseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const client = useQueryClient();
  const { token, user } = useAuth();
  const query = useCase(params.id);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [requestError, setRequestError] = useState<string | null>(null);
  const supervisor = Boolean(user?.roles.some((role) => ["AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role)));
  const canRequest = Boolean(user?.roles.some((role) => ["AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role)));
  const resolve = useMutation({ mutationFn: ({ resolutionCode, reason }: { resolutionCode: string; reason: string }) => api.post(`/duplicate-cases/${params.id}/resolve`, { resolutionCode, reason }, token), onSuccess: () => { setResolveOpen(false); void client.invalidateQueries({ queryKey: ["case", params.id] }); void client.invalidateQueries({ queryKey: ["cases"] }); }, });
  const requestInfo = useMutation({ mutationFn: () => api.post(`/duplicate-cases/${params.id}/request-information`, { reason: message.trim() }, token), onSuccess: () => { setRequestOpen(false); setMessage(""); void client.invalidateQueries({ queryKey: ["case", params.id] }); void client.invalidateQueries({ queryKey: ["cases"] }); }, onError: (err) => setRequestError(err instanceof ApiError ? err.message : "Could not request information.") });
  const item = query.data;
  if (query.isLoading) return <Skeleton className="h-96" />;
  if (query.error || !item) return <EmptyState title="Case unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load this case."} action={<Button variant="secondary" onClick={() => router.push("/aicte/cases")}>Back to cases</Button>} />;
  const responses = Array.isArray(item.evidence?.institutionResponses) ? item.evidence.institutionResponses : [];
  return <div className="space-y-5"><PageHeader eyebrow="National oversight · duplicate case" title={titleCase(item.matchType)} description={`${item.id} · institution ${item.institutionId ?? "unassigned"} · batch ${item.discoveredBatchId ?? "—"}`} actions={<Button variant="secondary" size="sm" onClick={() => router.push("/aicte/cases")} icon={<ArrowLeft className="size-4" />}>All cases</Button>} /><div className="flex flex-wrap items-center gap-2"><StatusBadge family="severity" status={item.severity} /><StatusBadge family="case" status={item.status} /><span className="text-xs text-ink-soft">Opened {formatDateTime(item.openedAt)}</span>{item.assignedReviewerId ? <span className="text-xs text-ink-soft">Assigned to {item.assignedReviewerId}</span> : null}</div><CaseEvidence caseItem={item} />{responses.length ? <Card><CardHeader><CardTitle>Institution responses</CardTitle></CardHeader><CardContent className="space-y-2 pt-3">{responses.map((response, index) => { const entry = response as { message?: string; by?: string; at?: string }; return <div key={`${entry.at ?? "response"}-${index}`} className="rounded-[8px] border border-border p-3"><p className="text-sm leading-6 text-ink">{entry.message}</p><p className="mt-1 text-[11px] text-ink-soft/70">{entry.by} · {entry.at}</p></div>; })}</CardContent></Card> : null}<Card><CardContent className="flex flex-wrap items-center justify-between gap-3 p-4"><div><p className="text-sm font-medium text-ink">Human review actions</p><p className="mt-1 text-xs text-ink-soft">Record reasoning; never auto-cancel or merge a student record.</p></div><div className="flex flex-wrap gap-2">{canRequest && item.status !== "RESOLVED" ? <Button variant="secondary" onClick={() => { setRequestError(null); setRequestOpen(true); }} icon={<MessageSquare className="size-4" />}>Request information</Button> : null}{supervisor && item.status !== "RESOLVED" ? <Button onClick={() => setResolveOpen(true)} icon={<ShieldCheck className="size-4" />}>Resolve case</Button> : null}{!supervisor && canRequest ? <span className="self-center text-[11px] text-ink-soft/70">Supervisor confirmation is required to resolve.</span> : null}</div></CardContent></Card><ResolutionDialog open={resolveOpen} onOpenChange={setResolveOpen} loading={resolve.isPending} error={resolve.error instanceof ApiError ? resolve.error.message : null} onResolve={async (resolutionCode, reason) => { await resolve.mutateAsync({ resolutionCode, reason }); }} /><Dialog open={requestOpen} onOpenChange={setRequestOpen} title="Request institution information" description="The institution will receive a notification and can respond with transfer or correction context." footer={<><Button variant="secondary" onClick={() => setRequestOpen(false)}>Cancel</Button><Button disabled={message.trim().length < 3} loading={requestInfo.isPending} onClick={() => { setRequestError(null); requestInfo.mutate(); }}>Send request</Button></>}><div className="space-y-3"><Textarea label="Information requested" required value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Please provide transfer evidence or explain the overlapping dates." />{requestError ? <p role="alert" className="text-sm text-danger">{requestError}</p> : null}</div></Dialog></div>;
}
