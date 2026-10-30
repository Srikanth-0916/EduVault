"use client";

import { Bell, Check, CheckCheck, ExternalLink, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { NotificationListResponse } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function NotificationsPage() {
  const { token } = useAuth();
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["notifications"], queryFn: () => api.get<NotificationListResponse>("/notifications?page=1&pageSize=50", token), enabled: Boolean(token) });
  async function markRead(id: string) { await api.post(`/notifications/${id}/read`, undefined, token); await client.invalidateQueries({ queryKey: ["notifications"] }); }
  async function markAll() { await api.post("/notifications/read-all", undefined, token); await client.invalidateQueries({ queryKey: ["notifications"] }); }
  const items = query.data?.items ?? [];
  return <div className="space-y-5"><PageHeader eyebrow="Workspace" title="Notifications" description="In-app events are delivered to the recipient account. Email channel entries are explicitly marked mock-only." actions={query.data?.unread ? <Button variant="secondary" size="sm" onClick={() => void markAll()} icon={<CheckCheck className="size-4" />}>Mark all read</Button> : null} />{query.isLoading ? <Skeleton className="h-80" /> : query.error ? <EmptyState title="Notifications unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load notifications."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : items.length ? <div className="space-y-2">{items.map((item) => <Card key={item.id} className={!item.readAt && item.channel === "IN_APP" ? "border-primary/25" : ""}><CardContent className="flex flex-wrap items-start gap-3 p-4"><span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary"><Bell className="size-4" /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-semibold text-ink">{item.title}</p>{item.channel === "EMAIL" ? <StatusBadge family="mock" status="MOCK" label={`Email ${item.deliveryStatus.toLowerCase()}`} /> : null}{!item.readAt && item.channel === "IN_APP" ? <span className="size-1.5 rounded-full bg-primary" aria-label="Unread" /> : null}</div><p className="mt-1 text-xs leading-5 text-ink-soft">{item.body}</p><p className="mt-1 text-[10px] text-ink-soft/70">{formatDateTime(item.createdAt)} · {item.eventType}</p>{item.resourceRef ? <Link href={item.resourceType === "submission_batch" ? `/institution/batches/${item.resourceRef}` : item.resourceType === "duplicate_case" ? `/institution/cases/${item.resourceRef}` : "/notifications"} className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline">Open related item <ExternalLink className="size-3" /></Link> : null}</div>{!item.readAt && item.channel === "IN_APP" ? <Button variant="ghost" size="sm" onClick={() => void markRead(item.id)} icon={<Check className="size-3.5" />}>Mark read</Button> : null}</CardContent></Card>)}</div> : <EmptyState icon={<Bell className="size-5" />} title="You’re all caught up" description="There are no notifications for this account." />}</div>;
}
