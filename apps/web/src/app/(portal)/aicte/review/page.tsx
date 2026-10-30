"use client";

import { RefreshCw } from "lucide-react";
import { Suspense, useState } from "react";

import { ReviewQueueTable } from "@/components/aicte/review-queue-table";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useReviewQueue, useReviewSummary } from "@/hooks/use-review";
import { ApiError } from "@/lib/api";
import { StatCard } from "@/components/ui/card";

function ReviewContent() {
  const [status, setStatus] = useState("UNDER_AICTE_REVIEW");
  const queue = useReviewQueue(status);
  const summary = useReviewSummary();
  return <div className="space-y-5">
    <PageHeader eyebrow="AICTE review" title="Review queue" description="Decide submitted batches without editing student fields. Reasons and reason codes are retained in the decision history." actions={<Select aria-label="Review queue status" value={status} onChange={(event) => setStatus(event.target.value)} containerClassName="w-52"><option value="UNDER_AICTE_REVIEW">Under review</option><option value="RETURNED_FOR_CORRECTION">Returned</option><option value="ACCEPTED">Accepted</option><option value="REJECTED">Rejected</option></Select>} />
    {summary.data ? <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5"><StatCard label="Under review" value={summary.data.underReview} tone="warning" /><StatCard label="Returned" value={summary.data.returned} /><StatCard label="Accepted" value={summary.data.accepted} tone="success" /><StatCard label="Rejected" value={summary.data.rejected} tone="danger" /><StatCard label="Open cases" value={summary.data.openCases} tone="warning" /></div> : null}
    <Card><CardContent className="p-4"><div className="flex items-center justify-between gap-3 text-xs text-ink-soft"><p>{queue.data?.total ?? 0} batch(es)</p><p>Reviewer queue is aggregate-first; open a batch for masked evidence.</p></div></CardContent></Card>
    {queue.isLoading ? <Skeleton className="h-80" /> : queue.error ? <EmptyState title="Queue unavailable" description={queue.error instanceof ApiError ? queue.error.message : "Could not load the review queue."} action={<Button variant="secondary" onClick={() => queue.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : <ReviewQueueTable items={queue.data?.items ?? []} />}
  </div>;
}

export default function ReviewQueuePage() { return <Suspense fallback={<Skeleton className="h-80" />}><ReviewContent /></Suspense>; }
