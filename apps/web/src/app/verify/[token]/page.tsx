"use client";

import { AlertOctagon, Loader2, ShieldCheck } from "lucide-react";
import { useParams } from "next/navigation";

import { VerificationResult } from "@/components/verify/verification-result";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { usePublicVerification } from "@/hooks/use-verification";
import { ApiError } from "@/lib/api";

export default function PublicVerifyPage() {
  const params = useParams<{ token: string }>();
  const query = usePublicVerification(params.token);
  if (query.isLoading) return <main className="flex min-h-screen items-center justify-center bg-canvas px-4"><div className="flex items-center gap-2 text-sm text-ink-soft"><Loader2 className="size-4 animate-spin text-primary" /> Checking verification reference…</div></main>;
  const denied = query.error instanceof ApiError || !query.data?.valid;
  return <main className="min-h-screen bg-canvas px-4 py-8 sm:px-6"><div className="mx-auto max-w-3xl space-y-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-primary">Controlled verification</p><h1 className="mt-1 font-display text-2xl font-semibold text-ink">APAAR-SDMV reference</h1></div><Badge tone="mock"><ShieldCheck className="size-3" /> Synthetic demo</Badge></div>{denied ? <Card className="border-danger/25"><CardContent className="flex items-start gap-3 p-6"><AlertOctagon className="mt-0.5 size-5 shrink-0 text-danger" /><div><h2 className="font-display text-lg font-semibold text-ink">Verification unavailable</h2><p className="mt-2 text-sm leading-6 text-ink-soft">This reference is expired, revoked, consumed or unavailable. No record details are disclosed.</p><p className="mt-4 text-xs leading-5 text-ink-soft/70">A denied reference does not reveal whether a student record existed.</p></div></CardContent></Card> : <VerificationResult data={query.data!} />}<p className="text-center text-[11px] leading-5 text-ink-soft/65">This prototype uses synthetic data and mock/sandbox external status. It is not a live government verification service.</p></div></main>;
}
