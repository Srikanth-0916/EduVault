import Link from "next/link";

import { ArrowRight, BadgeCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import type { StudentMeData } from "@/lib/types";

export function StudentRecordCard({ record }: { record: StudentMeData["enrollments"][number] }) {
  return <Card><CardContent className="flex flex-wrap items-center justify-between gap-4 p-4"><div><p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-primary">Current enrolment</p><p className="mt-1 text-sm font-semibold text-ink">{record.programmeId}</p><p className="mt-0.5 text-xs text-ink-soft">{record.institutionId} · {record.academicYear}</p></div><div className="flex flex-wrap items-center gap-2"><StatusBadge family="enrollment" status={record.enrollmentStatus} />{record.recordAccepted ? <Badge tone="success"><BadgeCheck className="size-3" /> AICTE accepted</Badge> : <Badge tone="neutral">Not accepted</Badge>}<Link href={`/institution/students/${record.id}`} className="ml-1 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">Details <ArrowRight className="size-3.5" /></Link></div></CardContent></Card>;
}
