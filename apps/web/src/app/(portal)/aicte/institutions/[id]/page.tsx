"use client";

import { ArrowLeft, BookOpen, Building, Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CapacityBar } from "@/components/institution/capacity-bar";
import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAcademicYear } from "@/hooks/use-academic-year";
import { useInstitutionDetail, useIntakeHistory } from "@/hooks/use-admin-data";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Campus, InstitutionDetail, Programme } from "@/lib/types";

function CampusDialog({ open, onOpenChange, institutionId, onCreated }: { open: boolean; onOpenChange: (open: boolean) => void; institutionId: string; onCreated: () => void }) {
  const { token } = useAuth();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({ mutationFn: () => api.post<Campus>(`/institutions/${institutionId}/campuses`, { campusCode: code.trim(), name: name.trim(), location: location.trim() || null }, token), onSuccess: () => { onOpenChange(false); onCreated(); }, onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create campus.") });
  return <Dialog open={open} onOpenChange={onOpenChange} title="Add campus" description="Campus master data is synthetic and all creation actions are audited." footer={<><Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button><Button disabled={code.trim().length < 2 || name.trim().length < 2} loading={mutation.isPending} onClick={() => mutation.mutate()}>Create campus</Button></>}><div className="space-y-4"><Input label="Campus code" required value={code} onChange={(event) => setCode(event.target.value)} /><Input label="Campus name" required value={name} onChange={(event) => setName(event.target.value)} /><Input label="Location" value={location} onChange={(event) => setLocation(event.target.value)} />{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}</div></Dialog>;
}

function ProgrammeDialog({ open, onOpenChange, campuses, onCreated }: { open: boolean; onOpenChange: (open: boolean) => void; campuses: Campus[]; onCreated: () => void }) {
  const { token } = useAuth();
  const [campusId, setCampusId] = useState(campuses[0]?.id ?? "");
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [award, setAward] = useState("UNDERGRADUATE");
  const [duration, setDuration] = useState("4");
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({ mutationFn: () => api.post<Programme>(`/campuses/${campusId}/programmes`, { programmeCode: code.trim(), programmeName: name.trim(), awardLevel: award, durationYears: Number(duration) }, token), onSuccess: () => { onOpenChange(false); onCreated(); }, onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create programme.") });
  return <Dialog open={open} onOpenChange={onOpenChange} title="Add programme" description="Programme master data does not create or change approved intake snapshots." footer={<><Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button><Button disabled={!campusId || code.trim().length < 1 || name.trim().length < 3} loading={mutation.isPending} onClick={() => mutation.mutate()}>Create programme</Button></>}><div className="space-y-4"><Select label="Campus" value={campusId} onChange={(event) => setCampusId(event.target.value)}>{campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}</Select><div className="grid gap-3 sm:grid-cols-2"><Input label="Programme code" required value={code} onChange={(event) => setCode(event.target.value)} /><Input label="Programme name" required value={name} onChange={(event) => setName(event.target.value)} /></div><div className="grid gap-3 sm:grid-cols-2"><Select label="Award level" value={award} onChange={(event) => setAward(event.target.value)}><option value="CERTIFICATE">Certificate</option><option value="DIPLOMA">Diploma</option><option value="PG_DIPLOMA">PG diploma</option><option value="UNDERGRADUATE">Undergraduate</option><option value="POSTGRADUATE">Postgraduate</option><option value="DOCTORAL">Doctoral</option></Select><Input label="Duration (years)" type="number" min={1} max={8} value={duration} onChange={(event) => setDuration(event.target.value)} /></div>{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}</div></Dialog>;
}

function InstitutionDetailContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [year, setYear] = useAcademicYear();
  const [campusOpen, setCampusOpen] = useState(false);
  const [programmeOpen, setProgrammeOpen] = useState(false);
  const query = useInstitutionDetail(params.id, year);
  const data = query.data;
  const history = useIntakeHistory(data?.programmes.map((item) => item.id) ?? []);
  const canManage = Boolean(user?.roles.some((role) => ["AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role)));
  function refresh() {
    void queryClient.invalidateQueries({ queryKey: ["aicte-institution", params.id] });
    void queryClient.invalidateQueries({ queryKey: ["aicte-institutions"] });
  }
  if (query.isLoading) return <Skeleton className="h-96" />;
  if (query.error || !data) return <EmptyState title="Institution unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load institution detail."} action={<Button variant="secondary" onClick={() => router.push("/aicte/institutions")}>Back to directory</Button>} />;
  return <div className="space-y-5"><PageHeader eyebrow="AICTE master data" title={data.name} description={`${data.aicteInstitutionCode} · ${data.city ?? "City not set"}${data.state ? `, ${data.state}` : ""}`} actions={<><Select aria-label="Academic year" value={year} onChange={(event) => setYear(event.target.value)} containerClassName="w-36"><option value="2025-26">2025-26</option><option value="2026-27">2026-27</option><option value="2027-28">2027-28</option></Select><Button variant="secondary" size="sm" onClick={() => router.push("/aicte/institutions")} icon={<ArrowLeft className="size-4" />}>Directory</Button></>} /><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Card><CardContent className="p-4"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Type</p><p className="mt-1 text-sm font-semibold text-ink">{data.institutionType.replaceAll("_", " ")}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Status</p><p className="mt-1"><Badge tone="success">{data.status}</Badge></p></CardContent></Card><Card><CardContent className="p-4"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Campuses</p><p className="mt-1 text-sm font-semibold tabular text-ink">{data.campuses.length}</p></CardContent></Card><Card><CardContent className="p-4"><p className="text-[10px] uppercase tracking-[0.07em] text-ink-soft/70">Programmes</p><p className="mt-1 text-sm font-semibold tabular text-ink">{data.programmes.length}</p></CardContent></Card></div><Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle className="flex items-center gap-2"><Building className="size-4 text-primary" />Campuses</CardTitle><CardDescription>Campus records are institution-scoped master data.</CardDescription></div>{canManage ? <Button size="sm" onClick={() => setCampusOpen(true)} icon={<Plus className="size-4" />}>Add campus</Button> : null}</CardHeader><CardContent className="grid gap-3 pt-4 md:grid-cols-2">{data.campuses.map((campus) => <div key={campus.id} className="rounded-[8px] border border-border p-3"><div className="flex justify-between gap-3"><p className="text-sm font-medium text-ink">{campus.name}</p><Badge tone="neutral">{campus.status}</Badge></div><p className="mt-1 text-xs text-ink-soft">{campus.campusCode} · {campus.location ?? "Location not set"}</p></div>)}</CardContent></Card><Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle className="flex items-center gap-2"><BookOpen className="size-4 text-primary" />Programmes & intake</CardTitle><CardDescription>Approved regular and authorized supernumerary allocations remain separate.</CardDescription></div>{canManage ? <Button size="sm" onClick={() => setProgrammeOpen(true)} icon={<Plus className="size-4" />}>Add programme</Button> : null}</CardHeader><CardContent className="space-y-4 pt-4">{data.programmes.map((programme) => { const snapshots = history.data?.[programme.id] ?? []; return <div key={programme.id} className="rounded-[10px] border border-border p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-medium text-ink">{programme.programmeName}</p><p className="text-xs text-ink-soft">{programme.programmeCode} · {programme.campusName} · {programme.awardLevel}</p></div><Link href={`/aicte/intake?programmeId=${programme.id}&academicYear=${year}`} className="text-xs font-semibold text-primary hover:underline">Manage intake history</Link></div><div className="mt-3"><CapacityBar approvedRegular={programme.approvedRegular} approvedSupernumerary={programme.approvedSupernumerary} reportedRegular={programme.reportedRegular} reportedSupernumerary={programme.reportedSupernumerary} status={programme.capacityStatus ?? "MISSING_APPROVAL_DATA"} /></div><div className="mt-3 border-t border-border pt-3"><p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.07em] text-ink-soft/65">Snapshot history</p>{snapshots.length ? <div className="space-y-1.5">{snapshots.slice(0, 4).map((snapshot) => <div key={snapshot.id} className="flex flex-wrap items-center justify-between gap-2 text-xs"><span className="text-ink">{snapshot.academicYear} · v{snapshot.version} · {snapshot.approvalReference}</span><StatusBadge family="case" status={snapshot.status === "ACTIVE" ? "OPEN" : "RESOLVED"} label={snapshot.status} /></div>)}</div> : <p className="text-xs text-ink-soft/70">No snapshots were returned for this programme.</p>}</div></div>; })}</CardContent></Card><CampusDialog open={campusOpen} onOpenChange={setCampusOpen} institutionId={data.id} onCreated={refresh} /><ProgrammeDialog open={programmeOpen} onOpenChange={setProgrammeOpen} campuses={data.campuses} onCreated={refresh} /></div>;
}

export default function InstitutionDetailPage() { return <Suspense fallback={<Skeleton className="h-96" />}><InstitutionDetailContent /></Suspense>; }
