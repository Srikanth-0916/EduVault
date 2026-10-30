"use client";

import { BookOpen, Info, RefreshCw } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { IntakeForm, type IntakeSnapshotPayload } from "@/components/aicte/intake-form";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useIntakeHistory } from "@/hooks/use-admin-data";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ApprovalSnapshot, Programme } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function IntakeContent() {
  const params = useSearchParams();
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const [year, setYear] = useAcademicYear();
  const [programmeId, setProgrammeId] = useState(params.get("programmeId") ?? "");
  const [error, setError] = useState<string | null>(null);
  const programmes = useQuery({ queryKey: ["all-programmes", year], queryFn: () => api.get<Programme[]>(`/programmes?academicYear=${encodeURIComponent(year)}`, token), enabled: Boolean(token) });
  const selectedId = programmeId || programmes.data?.[0]?.id || "";
  const programme = useMemo(() => programmes.data?.find((item) => item.id === selectedId) ?? null, [programmes.data, selectedId]);
  const history = useIntakeHistory(selectedId ? [selectedId] : []);
  const snapshots = history.data?.[selectedId] ?? [];
  const canEdit = Boolean(user?.roles.some((role) => ["AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role)));
  const create = useMutation({
    mutationFn: (payload: IntakeSnapshotPayload) => api.post<ApprovalSnapshot>(`/programmes/${selectedId}/intake-snapshots`, payload, token),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["intake-history"] }); void queryClient.invalidateQueries({ queryKey: ["all-programmes"] }); void queryClient.invalidateQueries({ queryKey: ["aicte-institution"] }); },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create the intake snapshot."),
  });

  return <div className="space-y-5"><PageHeader eyebrow="AICTE master data" title="Approved intake snapshots" description="Create versioned approval evidence. Regular seats and separately authorized supernumerary seats are never combined." actions={<Select aria-label="Academic year" value={year} onChange={(event) => setYear(event.target.value)} containerClassName="w-36"><option value="2025-26">2025-26</option><option value="2026-27">2026-27</option><option value="2027-28">2027-28</option></Select>} /><Card className="border-primary/20 bg-primary-soft/25"><CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#115e59]"><Info className="mt-0.5 size-4 shrink-0" /><p>Creating a new snapshot supersedes the old active snapshot but preserves its history. Institution users cannot edit regulatory master data.</p></CardContent></Card>{programmes.isLoading ? <Skeleton className="h-72" /> : programmes.error ? <EmptyState title="Programmes unavailable" description={programmes.error instanceof ApiError ? programmes.error.message : "Could not load programmes."} action={<Button variant="secondary" onClick={() => programmes.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : !programmes.data?.length ? <EmptyState title="No programmes" description="Create an institution, campus and programme before adding intake approval." icon={<BookOpen className="size-5" />} /> : <><Card><CardContent className="grid gap-3 p-4 md:grid-cols-2"><Select label="Programme" value={selectedId} onChange={(event) => setProgrammeId(event.target.value)}>{programmes.data.map((item) => <option key={item.id} value={item.id}>{item.programmeCode} — {item.programmeName} · {item.institutionName}</option>)}</Select><div className="rounded-[8px] border border-border bg-surface-muted/35 px-3 py-2"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/65">Current capacity state</p><div className="mt-1 flex items-center gap-2"><span className="text-xs font-medium text-ink">{programme?.campusName}</span>{programme?.capacityStatus ? <StatusBadge family="capacity" status={programme.capacityStatus} /> : null}</div></div></CardContent></Card><div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">{programme ? <Card><CardHeader><CardTitle>Create a new snapshot</CardTitle><CardDescription>{programme.programmeName} · {year}</CardDescription></CardHeader><CardContent className="pt-3">{canEdit ? <IntakeForm key={`${programme.id}-${year}`} programme={programme} academicYear={year} loading={create.isPending} error={error ?? (create.error instanceof ApiError ? create.error.message : null)} onSubmit={async (payload) => { setError(null); await create.mutateAsync(payload); }} /> : <p className="rounded-[8px] border border-border bg-surface-muted/40 p-3 text-xs leading-5 text-ink-soft">Read-only for this role. AICTE supervisors and system administrators can create approval snapshots.</p>}</CardContent></Card> : null}<Card><CardHeader><CardTitle>Snapshot history</CardTitle><CardDescription>Latest versions first; previous approvals remain preserved.</CardDescription></CardHeader><CardContent className="space-y-3 pt-3">{history.isLoading ? <Skeleton className="h-40" /> : history.error ? <p className="text-sm text-danger">{history.error instanceof ApiError ? history.error.message : "History unavailable."}</p> : snapshots.length ? snapshots.map((snapshot) => <div key={snapshot.id} className="rounded-[9px] border border-border p-3"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-sm font-semibold text-ink">{snapshot.academicYear} · version {snapshot.version}</p><p className="mt-0.5 text-xs text-ink-soft">{snapshot.approvalReference} · valid from {formatDate(snapshot.validFrom)}</p></div><StatusBadge family="case" status={snapshot.status === "ACTIVE" ? "OPEN" : "RESOLVED"} label={snapshot.status} /></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{snapshot.allocations.map((allocation) => <div key={allocation.id} className="rounded-[7px] bg-surface-muted/50 px-2.5 py-2 text-xs"><p className="text-ink-soft">{allocation.seatClassification === "APPROVED_REGULAR" ? "Regular approved" : allocation.seatClassification === "APPROVED_SUPERNUMERARY" ? "Authorized supernumerary" : allocation.seatClassification}</p><p className="mt-0.5 font-semibold tabular text-ink">{allocation.approvedCount.toLocaleString("en-IN")} seats</p>{allocation.authorizationReference ? <p className="mt-0.5 break-all text-[10px] text-ink-soft/70">Authorization: {allocation.authorizationReference}</p> : null}</div>)}</div>{snapshot.notes ? <p className="mt-2 text-[11px] text-ink-soft/75">{snapshot.notes}</p> : null}</div>) : <p className="text-xs text-ink-soft">No approval snapshots available for this programme.</p>}</CardContent></Card></div></>}</div>;
}

export default function IntakePage() { return <Suspense fallback={<Skeleton className="h-96" />}><IntakeContent /></Suspense>; }
