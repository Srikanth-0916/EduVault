"use client";

import { CheckCircle2, Copy, Download, Link2, Plus, QrCode } from "lucide-react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ShareList } from "@/components/student/share-list";
import { QrDialog } from "@/components/student/qr-dialog";
import { ShareWizard, type ShareWizardValues } from "@/components/student/share-wizard";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyVerificationRequests } from "@/hooks/use-verification";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AuthorizeResponse } from "@/lib/types";

export default function StudentSharingPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const requests = useMyVerificationRequests();
  const [wizardOpen, setWizardOpen] = useState(false);
  const [result, setResult] = useState<AuthorizeResponse | null>(null);
  const [qrOpen, setQrOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const create = useMutation({
    mutationFn: async (values: ShareWizardValues) => {
      const request = await api.post<{ id: string }>("/verification-requests", values, token);
      return api.post<AuthorizeResponse>(`/verification-requests/${request.id}/authorize`, undefined, token);
    },
    onSuccess: (next) => { setResult(next); setWizardOpen(false); void queryClient.invalidateQueries({ queryKey: ["verification-requests"] }); void queryClient.invalidateQueries({ queryKey: ["student-me"] }); },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create the share."),
  });
  const revoke = useMutation({
    mutationFn: (id: string) => api.post(`/verification-requests/${id}/revoke`, { reason: "Revoked by student" }, token),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["verification-requests"] }); void queryClient.invalidateQueries({ queryKey: ["student-me"] }); },
  });
  async function copy(value: string) { await navigator.clipboard?.writeText(value); }
  function downloadReceipt() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result.receipt, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${result.request.id}-consent-receipt.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (requests.isLoading) return <Skeleton className="h-96" />;
  if (requests.error) return <EmptyState title="Sharing unavailable" description={requests.error instanceof ApiError ? requests.error.message : "Could not load shares."} />;
  return <div className="space-y-5"><PageHeader eyebrow="Student portal" title="Sharing" description="Create expiring, purpose-bound links. Verifiers receive no search or bulk lookup access." actions={<Button onClick={() => { setError(null); setWizardOpen(true); }} icon={<Plus className="size-4" />}>Create share</Button>} />{error ? <p role="alert" className="rounded-[8px] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p> : null}{result ? <Card className="border-success/25 bg-success-soft/30"><CardContent className="space-y-3 p-4"><div className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 size-5 text-success" /><div><p className="font-semibold text-ink">Share authorized</p><p className="mt-1 text-xs text-ink-soft">Send this link only to {result.request.recipientName}. It expires {new Date(result.expiresAt).toLocaleString("en-IN")}.</p></div><Badge tone="success">{result.request.requestedClaims.length} claims</Badge></div><div className="flex flex-wrap items-center gap-2 rounded-[8px] border border-success/25 bg-surface p-2"><code className="min-w-0 flex-1 break-all text-[11px] text-ink">{result.verifyUrl}</code><Button variant="secondary" size="sm" onClick={() => copy(result.verifyUrl)} icon={<Copy className="size-3.5" />}>Copy link</Button><Button variant="secondary" size="sm" onClick={() => setQrOpen(true)} icon={<QrCode className="size-3.5" />}>Show QR</Button><Button variant="ghost" size="sm" onClick={downloadReceipt} icon={<Download className="size-3.5" />}>Receipt</Button></div><p className="text-[11px] text-ink-soft/75">The QR contains only an opaque token. Claims remain on the server until the purpose-bound reference is resolved.</p></CardContent></Card> : null}<Card><CardHeader><CardTitle>My shares</CardTitle><CardDescription>Revocation stops future public access.</CardDescription></CardHeader><CardContent className="pt-3"><ShareList requests={requests.data?.items ?? []} /></CardContent></Card><ShareWizard open={wizardOpen} onOpenChange={setWizardOpen} loading={create.isPending} error={create.error instanceof ApiError ? create.error.message : null} onSubmit={async (values) => { setError(null); await create.mutateAsync(values); }} />{result ? <QrDialog open={qrOpen} onOpenChange={setQrOpen} url={result.verifyUrl} /> : null}</div>;
}
