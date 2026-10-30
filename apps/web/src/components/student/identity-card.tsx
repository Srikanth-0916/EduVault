import { FlaskConical, ShieldCheck } from "lucide-react";

import { IdentityStatus } from "@/components/institution/identity-status";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StudentMeData } from "@/lib/types";

export function StudentIdentityCard({ student }: { student: StudentMeData }) {
  return <Card><CardHeader><CardTitle>Identity summary</CardTitle></CardHeader><CardContent className="space-y-4 pt-3"><div className="flex flex-wrap items-start justify-between gap-4 rounded-[10px] border border-border bg-surface-muted/35 p-4"><div><p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-ink-soft/70">APAAR display</p><p className="mt-1 font-mono text-xl text-ink">{student.maskedApaar}</p><p className="mt-1 text-[11px] text-ink-soft/70">Last four only. The full value is never displayed.</p></div><IdentityStatus status={student.identityStatus} /></div><div className="grid gap-3 sm:grid-cols-2"><div className="rounded-[8px] border border-border p-3"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Format check</p><p className="mt-1 text-xs text-ink">{student.identityStatus === "FORMAT_VALID" || student.identityStatus === "EXTERNALLY_CONFIRMED" ? "Format valid" : student.identityStatus}</p></div><div className="rounded-[8px] border border-dashed border-accent/35 bg-accent-soft/30 p-3"><p className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.07em] text-[#92400e]"><FlaskConical className="size-3" />External check</p><p className="mt-1 text-xs text-[#92400e]">Mock/sandbox only</p></div></div><p className="flex items-start gap-2 text-xs leading-5 text-ink-soft"><ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />Record acceptance is a separate AICTE workflow outcome shown on each enrolment below.</p></CardContent></Card>;
}
