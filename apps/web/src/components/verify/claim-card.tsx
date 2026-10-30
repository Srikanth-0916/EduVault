import { CheckCircle2, FlaskConical } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { PublicClaim } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

export function ClaimCard({ claim }: { claim: PublicClaim }) {
  const mock = claim.source === "MOCK_APAAR";
  return <Card><CardContent className="p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-ink-soft/70">{claim.label}</p><p className="mt-1 text-base font-semibold text-ink">{claim.value}</p></div><Badge tone={mock ? "mock" : "success"}>{mock ? <FlaskConical className="size-3" /> : <CheckCircle2 className="size-3" />} {mock ? "Mock status" : titleCase(claim.status)}</Badge></div><div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-ink-soft/70"><span>Source: {claim.source}</span>{claim.asOf ? <><span aria-hidden="true">·</span><span>As of {formatDateTime(claim.asOf)}</span></> : null}</div></CardContent></Card>;
}
