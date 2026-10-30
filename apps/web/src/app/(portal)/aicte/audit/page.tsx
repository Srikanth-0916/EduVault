"use client";

import { Eye, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AuditEvent, AuditListResponse } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function AicteAuditPage() {
  const { token } = useAuth();
  const [action, setAction] = useState("");
  const [actorId, setActorId] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [resourceRef, setResourceRef] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [selected, setSelected] = useState<AuditEvent | null>(null);
  const params = new URLSearchParams({ page: "1", pageSize: "50" });
  if (action.trim()) params.set("action", action.trim());
  if (actorId.trim()) params.set("actorId", actorId.trim());
  if (resourceType.trim()) params.set("resourceType", resourceType.trim());
  if (resourceRef.trim()) params.set("resourceRef", resourceRef.trim());
  if (from) params.set("from", new Date(from).toISOString());
  if (to) params.set("to", new Date(to).toISOString());
  const query = useQuery({ queryKey: ["audit-events", params.toString()], queryFn: () => api.get<AuditListResponse>(`/audit-events?${params.toString()}`, token), enabled: Boolean(token) });

  return <div className="space-y-5"><PageHeader eyebrow="Accountability" title="Audit trail" description="Append-only event history. Metadata is sanitized before it is stored and is sanitized again for display." /><Card><CardHeader><CardTitle>Filters</CardTitle><CardDescription>Filter by actor, action, resource or timestamp window.</CardDescription></CardHeader><CardContent className="grid gap-3 pt-4 md:grid-cols-2 xl:grid-cols-3"><Input label="Action" value={action} onChange={(event) => setAction(event.target.value)} placeholder="REPORT_EXPORTED" /><Input label="Actor ID" value={actorId} onChange={(event) => setActorId(event.target.value)} placeholder="usr_…" /><Input label="Resource type" value={resourceType} onChange={(event) => setResourceType(event.target.value)} placeholder="submission_batch" /><Input label="Resource reference" value={resourceRef} onChange={(event) => setResourceRef(event.target.value)} /><Input label="From" type="datetime-local" value={from} onChange={(event) => setFrom(event.target.value)} /><Input label="To" type="datetime-local" value={to} onChange={(event) => setTo(event.target.value)} /></CardContent></Card>{query.isLoading ? <Skeleton className="h-80" /> : query.error ? <EmptyState title="Audit trail unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load audit events."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : query.data?.items.length ? <Card><CardHeader className="flex-row items-center justify-between"><div><CardTitle>Audit events</CardTitle><CardDescription>{query.data.total} event(s)</CardDescription></div><Button variant="secondary" size="sm" onClick={() => query.refetch()} icon={<Search className="size-3.5" />}>Apply filters</Button></CardHeader><CardContent className="pt-3"><div className="overflow-hidden rounded-[10px] border border-border"><Table><TableHeader><TableRow><TableHead>Timestamp</TableHead><TableHead>Actor</TableHead><TableHead>Action</TableHead><TableHead>Resource</TableHead><TableHead>Outcome</TableHead><TableHead className="text-right">Detail</TableHead></TableRow></TableHeader><TableBody>{query.data.items.map((event) => <TableRow key={event.id} onClick={() => setSelected(event)} className="cursor-pointer"><TableCell className="whitespace-nowrap text-xs text-ink-soft">{formatDateTime(event.timestamp)}</TableCell><TableCell><p className="text-xs font-medium text-ink">{event.actorEmail ?? event.actorId ?? "System"}</p><p className="text-[10px] text-ink-soft/70">{event.actorRole ?? "—"}</p></TableCell><TableCell className="font-mono text-[11px] text-ink">{event.action}</TableCell><TableCell><p className="text-xs text-ink">{event.resourceType}</p><p className="max-w-40 truncate font-mono text-[10px] text-ink-soft/70">{event.resourceRef ?? "—"}</p></TableCell><TableCell><StatusBadge family="case" status={event.outcome === "SUCCESS" ? "RESOLVED" : "OPEN"} label={event.outcome} /></TableCell><TableCell className="text-right"><Button variant="ghost" size="sm" onClick={(eventClick) => { eventClick.stopPropagation(); setSelected(event); }} icon={<Eye className="size-3.5" />}>View</Button></TableCell></TableRow>)}</TableBody></Table></div></CardContent></Card> : <EmptyState title="No audit events" description="No events match the selected filters." />}
    <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} title="Audit event detail" description="Read-only evidence; no edit or delete controls are available."><div className="space-y-3">{selected ? <><dl className="grid gap-x-5 gap-y-2 text-xs sm:grid-cols-2"><div><dt className="text-ink-soft">Action</dt><dd className="mt-0.5 font-mono text-ink">{selected.action}</dd></div><div><dt className="text-ink-soft">Timestamp</dt><dd className="mt-0.5 text-ink">{formatDateTime(selected.timestamp)}</dd></div><div><dt className="text-ink-soft">Actor</dt><dd className="mt-0.5 text-ink">{selected.actorEmail ?? selected.actorId ?? "System"}</dd></div><div><dt className="text-ink-soft">Resource</dt><dd className="mt-0.5 break-all font-mono text-ink">{selected.resourceType} · {selected.resourceRef}</dd></div><div><dt className="text-ink-soft">Outcome</dt><dd className="mt-0.5 text-ink">{selected.outcome}</dd></div><div><dt className="text-ink-soft">Reason</dt><dd className="mt-0.5 text-ink">{selected.reason ?? "—"}</dd></div></dl><div><p className="mb-1 text-xs font-semibold text-ink">Sanitized metadata</p><pre className="max-h-72 overflow-auto rounded-[8px] border border-border bg-surface-muted/50 p-3 text-[10px] leading-5 text-ink-soft">{JSON.stringify(selected.metadata ?? {}, null, 2)}</pre></div></> : null}</div></Dialog></div>;
}
