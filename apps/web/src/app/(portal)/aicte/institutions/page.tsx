"use client";

import { Building2, Plus, RefreshCw, Search } from "lucide-react";
import Link from "next/link";
import { Suspense, useDeferredValue, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useInstitutions } from "@/hooks/use-admin-data";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { UserContextInstitution } from "@/lib/types";

function CreateInstitutionDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}) {
  const { token } = useAuth();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [type, setType] = useState("PRIVATE_SELF_FINANCED");
  const [stateName, setStateName] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: () => api.post<UserContextInstitution>("/institutions", {
      aicteInstitutionCode: code.trim(),
      name: name.trim(),
      institutionType: type,
      state: stateName.trim() || null,
      city: city.trim() || null,
    }, token),
    onSuccess: () => { onOpenChange(false); onCreated(); },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create institution."),
  });
  return <Dialog open={open} onOpenChange={onOpenChange} title="Create synthetic institution" description="Master-data changes are audited and should use synthetic demonstration records." footer={<><Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button><Button disabled={code.trim().length < 3 || name.trim().length < 3} loading={mutation.isPending} onClick={() => { setError(null); mutation.mutate(); }}>Create institution</Button></>}><div className="space-y-4"><Input label="AICTE institution code" required value={code} onChange={(event) => setCode(event.target.value)} /><Input label="Institution name" required value={name} onChange={(event) => setName(event.target.value)} /><Select label="Institution type" value={type} onChange={(event) => setType(event.target.value)}><option value="GOVERNMENT">Government</option><option value="GOVERNMENT_AIDED">Government aided</option><option value="PRIVATE_SELF_FINANCED">Private self-financed</option><option value="DEEMED_UNIVERSITY">Deemed university</option><option value="OTHER">Other</option></Select><div className="grid gap-3 sm:grid-cols-2"><Input label="State" value={stateName} onChange={(event) => setStateName(event.target.value)} /><Input label="City" value={city} onChange={(event) => setCity(event.target.value)} /></div>{error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}</div></Dialog>;
}

function DirectoryContent() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const query = useInstitutions(deferredSearch);
  const rows = (query.data?.items ?? []).filter((item) => (!typeFilter || item.institutionType === typeFilter) && (!stateFilter || item.state === stateFilter));
  const canCreate = Boolean(user?.roles.some((role) => ["AICTE_SUPERVISOR", "SYSTEM_ADMIN"].includes(role)));
  const states = Array.from(new Set((query.data?.items ?? []).map((item) => item.state).filter((value): value is string => Boolean(value)))).sort();

  return <div className="space-y-5"><PageHeader eyebrow="AICTE master data" title="Institution directory" description="Browse synthetic institutions, campuses, programmes and approval evidence. Master-data mutations are restricted to supervisors and system administrators." actions={canCreate ? <Button onClick={() => setCreateOpen(true)} icon={<Plus className="size-4" />}>Create institution</Button> : null} /><Card><CardContent className="grid gap-3 p-4 md:grid-cols-3"><Input aria-label="Search institutions" placeholder="Search name, code or city" value={search} onChange={(event) => setSearch(event.target.value)} leading={<Search className="size-4" />} /><Select aria-label="Filter institution type" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}><option value="">All institution types</option><option value="GOVERNMENT">Government</option><option value="GOVERNMENT_AIDED">Government aided</option><option value="PRIVATE_SELF_FINANCED">Private self-financed</option><option value="DEEMED_UNIVERSITY">Deemed university</option><option value="OTHER">Other</option></Select><Select aria-label="Filter state" value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}><option value="">All states</option>{states.map((state) => <option key={state} value={state}>{state}</option>)}</Select></CardContent></Card>{query.isLoading ? <Skeleton className="h-80" /> : query.error ? <EmptyState title="Directory unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load the institution directory."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : rows.length ? <><p className="text-xs text-ink-soft">Showing {rows.length} institution(s) · {query.data?.total ?? rows.length} total</p><div className="grid gap-3 lg:grid-cols-2">{rows.map((item) => <Link key={item.id} href={`/aicte/institutions/${item.id}`} className="rounded-[12px] border border-border bg-surface p-4 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-pop"><div className="flex items-start justify-between gap-3"><div className="flex min-w-0 items-start gap-3"><span className="flex size-10 shrink-0 items-center justify-center rounded-[9px] bg-primary-soft text-primary"><Building2 className="size-5" /></span><div className="min-w-0"><p className="truncate font-semibold text-ink">{item.name}</p><p className="mt-0.5 text-xs text-ink-soft">{item.aicteInstitutionCode} · {item.city ?? "City not set"}{item.state ? `, ${item.state}` : ""}</p></div></div><Badge tone="neutral">{item.status}</Badge></div><div className="mt-4 flex flex-wrap gap-2"><Badge tone="info">{item.institutionType.replaceAll("_", " ")}</Badge><Badge tone="neutral">{item.campusCount} campuses</Badge><Badge tone="neutral">{item.programmeCount} programmes</Badge></div></Link>)}</div></> : <EmptyState title="No institutions match" description="Change your search or filters, or create a synthetic institution if your role allows it." />}<CreateInstitutionDialog open={createOpen} onOpenChange={setCreateOpen} onCreated={() => void queryClient.invalidateQueries({ queryKey: ["aicte-institutions"] })} /></div>;
}

export default function AicteInstitutionsPage() { return <Suspense fallback={<Skeleton className="h-80" />}><DirectoryContent /></Suspense>; }
