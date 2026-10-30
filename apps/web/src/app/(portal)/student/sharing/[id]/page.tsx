"use client";

import { ArrowLeft, Copy, ShieldOff } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import { ApiError, api } from "@/lib/api";
import type { VerificationRequest } from "@/lib/types";

export default function ShareDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [link, setLink] = useState<string | null>(null);
  const query = useQuery({ queryKey: ["verification-request", params.id], queryFn: () => api.get<VerificationRequest>(`/verification-requests/${params.id}`, token), enabled: Boolean(token && params.id) });
  const issue = useMutation({ mutationFn: () => api.post<{ verifyUrl: string }>(`/verification-requests/${params.id}/issue-link`, undefined, token), onSuccess: (next) => setLink(next.verifyUrl) });
  const revoke = useMutation({ mutationFn: () => api.post(`/verification-requests/${params.id}/revoke`, { reason: "Revoked by student" }, token), onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["verification-request", params.id] }); void queryClient.invalidateQueries({ queryKey: ["verification-requests"] }); } });
  if (query.isLoading) return <Skeleton className="h-80" />;
  if (query.error || !query.data) return <EmptyState title="Share unavailable" description={query.error instanceof ApiError ? query.error.message : "The share could not be loaded."} />;
  const item = query.data;
  return <div className="space-y-5"><PageHeader eyebrow="Student portal · sharing" title={item.recipientName} description={`${item.recipientOrg} · ${item.purpose}`} actions={<Button variant="secondary" size="sm" onClick={() => router.push("/student/sharing")} icon={<ArrowLeft className="size-4" />}>All shares</Button>} /><div className="flex flex-wrap items-center gap-2"><StatusBadge family="verification" status={item.status} /><span className="text-xs text-ink-soft">{item.requestedClaims.length} selected claim(s)</span></div><Card><CardHeader><CardTitle>Authorized fields</CardTitle></CardHeader><CardContent className="flex flex-wrap gap-2 pt-3">{item.requestedClaims.map((claim) => <span key={claim} className="rounded-full bg-primary-soft px-2.5 py-1 font-mono text-[11px] text-primary">{claim}</span>)}</CardContent></Card>{link ? <Card className="border-primary/25 bg-primary-soft/25"><CardContent className="flex flex-wrap items-center gap-3 p-4"><code className="min-w-0 flex-1 break-all text-xs text-ink">{link}</code><Button variant="secondary" size="sm" onClick={() => navigator.clipboard?.writeText(link)} icon={<Copy className="size-3.5" />}>Copy</Button></CardContent></Card> : null}<div className="flex flex-wrap gap-2">{item.status !== "REVOKED" ? <Button variant="secondary" loading={issue.isPending} onClick={() => issue.mutate()}>Issue fresh link</Button> : null}{item.status !== "REVOKED" ? <Button variant="dangerOutline" loading={revoke.isPending} onClick={() => { if (window.confirm("Revoke this share? Future public access will stop.")) revoke.mutate(); }} icon={<ShieldOff className="size-4" />}>Revoke access</Button> : null}</div><p className="text-xs leading-5 text-ink-soft">The public verifier sees only the claims above. It cannot discover additional records, full APAAR, or the student name.</p></div>;
}
