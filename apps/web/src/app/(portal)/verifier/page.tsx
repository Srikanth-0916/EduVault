"use client";

import { ArrowRight, ScanLine } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";

export default function VerifierPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [reference, setReference] = useState("");
  const [error, setError] = useState<string | null>(null);
  function open() {
    setError(null);
    const value = reference.trim();
    if (!value) { setError("Paste a verification link or token."); return; }
    const token = value.includes("/verify/") ? value.split("/verify/").pop() : value;
    if (!token) { setError("That reference is not valid."); return; }
    router.push(`/verify/${encodeURIComponent(token)}`);
  }
  return <div className="space-y-5"><PageHeader eyebrow="Verifier access" title="Verify a reference" description={`Signed in as ${user?.email ?? "external verifier"}. A verifier can resolve only a link shared for a stated purpose; there is no search or bulk lookup.`} /><Card className="max-w-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><ScanLine className="size-4 text-primary" />Paste a verification reference</CardTitle></CardHeader><CardContent className="space-y-4 pt-3"><Textarea label="Verification link or opaque token" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="https://…/verify/opaque-token" hint="The token contains no claims or student identifier." />{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}<div className="flex justify-end"><Button onClick={open} icon={<ArrowRight className="size-4" />}>Open reference</Button></div></CardContent></Card><p className="max-w-2xl text-xs leading-5 text-ink-soft">The result will show claim-by-claim source and status, expiry, and a signed prototype receipt. Expired or revoked links fail closed without disclosing details.</p></div>;
}
