"use client";

import { Link2, RefreshCw, ShieldCheck, UserRound } from "lucide-react";
import Link from "next/link";

import { StudentIdentityCard } from "@/components/student/identity-card";
import { StudentRecordCard } from "@/components/student/record-card";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useStudentMe } from "@/hooks/use-student";
import { ApiError } from "@/lib/api";

export default function StudentRecordPage() {
  const query = useStudentMe();
  if (query.isLoading) return <Skeleton className="h-96" />;
  if (query.error || !query.data) return <EmptyState title="Record unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load your record."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} />;
  const student = query.data;
  return <div className="space-y-5"><PageHeader eyebrow="Student portal" title="My record" description="Review the institution-submitted record and share only the claims you authorize." actions={<Link href="/student/sharing"><Button icon={<Link2 className="size-4" />}>Create a share</Button></Link>} /><div className="rounded-[10px] border border-primary/20 bg-primary-soft/30 p-4 text-xs leading-5 text-[#115e59]"><p className="flex items-center gap-2 font-semibold"><ShieldCheck className="size-4" /> Separate status signals</p><p className="mt-1">APAAR format, mock external status and AICTE acceptance are shown independently. This prototype contains synthetic data only.</p></div><div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]"><StudentIdentityCard student={student} /><Card><CardHeader><CardTitle>Current enrolments</CardTitle><CardDescription>Institution-submitted records and AICTE acceptance state.</CardDescription></CardHeader><CardContent className="space-y-2 pt-3">{student.enrollments.length ? student.enrollments.map((record) => <StudentRecordCard key={record.id} record={record} />) : <EmptyState icon={<UserRound className="size-5" />} title="No current enrolment" description="No current institution-submitted enrolment is linked to this identity." />}</CardContent></Card></div><Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle>Recent shares</CardTitle><CardDescription>Purpose-bound access links and their current status.</CardDescription></div><Link href="/student/sharing" className="text-xs font-semibold text-primary hover:underline">Manage sharing</Link></CardHeader><CardContent className="pt-3">{student.verificationRequests.length ? <div className="space-y-2">{student.verificationRequests.slice(0, 3).map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[8px] border border-border px-3 py-2.5"><div><p className="text-sm font-medium text-ink">{item.recipientName}</p><p className="text-xs text-ink-soft">{item.purpose}</p></div><span className="rounded-full border border-border px-2 py-0.5 text-[11px] text-ink-soft">{item.status}</span></div>)}</div> : <p className="text-xs text-ink-soft">No shares have been created.</p>}</CardContent></Card></div>;
}
