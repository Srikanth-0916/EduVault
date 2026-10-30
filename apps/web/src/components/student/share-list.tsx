import Link from "next/link";

import { ArrowRight, Link2 } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { VerificationRequest } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function ShareList({ requests }: { requests: VerificationRequest[] }) {
  if (!requests.length) return <EmptyState icon={<Link2 className="size-5" />} title="No shares yet" description="Create a purpose-bound share when a verifier needs selected claims from your record." />;
  return <div className="space-y-2">{requests.map((item) => <Link key={item.id} href={`/student/sharing/${item.id}`} className="flex items-center justify-between gap-3 rounded-[10px] border border-border bg-surface px-3 py-3 shadow-card hover:border-primary/35"><div><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-medium text-ink">{item.recipientName}</p><StatusBadge family="verification" status={item.status} /></div><p className="mt-1 text-xs text-ink-soft">{item.recipientOrg} · {item.purpose}</p><p className="mt-1 text-[11px] text-ink-soft/70">{item.requestedClaims.length} claim(s) · created {formatDateTime(item.createdAt)}</p></div><ArrowRight className="size-4 shrink-0 text-primary" /></Link>)}</div>;
}
