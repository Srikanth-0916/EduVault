"use client";

import { Download, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CURRENT_ACADEMIC_YEAR } from "@/hooks/use-academic-year";
import { API_BASE_URL, ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ReportEnvelope } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

type ReportKey = "enrolment" | "intake-reconciliation" | "data-quality";
const REPORTS: { key: ReportKey; label: string }[] = [
  { key: "enrolment", label: "Enrolment" },
  { key: "intake-reconciliation", label: "Intake reconciliation" },
  { key: "data-quality", label: "Data quality" },
];

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function AicteReportsPage() {
  const { token, user } = useAuth();
  const [report, setReport] = useState<ReportKey>("enrolment");
  const [year, setYear] = useState(CURRENT_ACADEMIC_YEAR);
  const [groupBy, setGroupBy] = useState("institution");
  const [error, setError] = useState<string | null>(null);
  const path = report === "enrolment"
    ? `/reports/enrolment?academicYear=${encodeURIComponent(year)}&groupBy=${groupBy}`
    : `/reports/${report}?academicYear=${encodeURIComponent(year)}`;
  const query = useQuery({ queryKey: ["report", report, year, groupBy], queryFn: () => api.get<ReportEnvelope>(path, token), enabled: Boolean(token) });
  const analyst = Boolean(user?.roles.includes("AICTE_ANALYST") && !user.roles.some((role) => ["AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN", "AUDITOR"].includes(role)));
  const items = query.data?.items ?? [];
  const columns = Array.from(new Set(items.flatMap((item) => Object.keys(item)))).filter((key) => !["evidence"].includes(key));

  async function download() {
    setError(null);
    const exportPath = report === "enrolment"
      ? `/reports/enrolment/export.csv?academicYear=${encodeURIComponent(year)}&groupBy=${groupBy}`
      : `/reports/${report}/export.csv?academicYear=${encodeURIComponent(year)}`;
    try {
      const response = await fetch(`${API_BASE_URL}${exportPath}`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "text/csv" },
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new ApiError(payload?.error?.message ?? "Could not download this report.", response.status, payload?.error?.code);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${report}-${year}.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not download this report.");
    }
  }

  return <div className="space-y-5"><PageHeader eyebrow="AICTE oversight" title="Reports & reconciliation" description="Aggregate reporting is role-scoped, small groups are suppressed for analysts, and every CSV export is audited." actions={<><Select aria-label="Academic year" value={year} onChange={(event) => setYear(event.target.value)} containerClassName="w-36"><option value="2025-26">2025-26</option><option value="2026-27">2026-27</option><option value="2027-28">2027-28</option></Select>{report === "enrolment" ? <Select aria-label="Group report by" value={groupBy} onChange={(event) => setGroupBy(event.target.value)} containerClassName="w-40"><option value="institution">Institution</option><option value="programme">Programme</option></Select> : null}<Button variant="secondary" size="sm" onClick={download} icon={<Download className="size-4" />}>Export audited CSV</Button></>} />
    <div role="tablist" aria-label="Report type" className="flex flex-wrap gap-2">{REPORTS.map((item) => <button key={item.key} role="tab" aria-selected={report === item.key} onClick={() => setReport(item.key)} className={`rounded-[8px] border px-3 py-2 text-xs font-medium ${report === item.key ? "border-primary bg-primary-soft text-primary" : "border-border bg-surface text-ink-soft hover:bg-surface-muted"}`}>{item.label}</button>)}</div>
    <Card><CardContent className="flex flex-wrap items-center justify-between gap-3 p-4"><div><p className="text-sm font-medium text-ink">Privacy and provenance</p><p className="mt-1 text-xs leading-5 text-ink-soft">{analyst ? "Analyst view is aggregate-only. Groups below five are suppressed." : "This view contains aggregate summaries only; student names and APAAR identifiers are excluded."}</p></div><Badge tone="mock">Synthetic data</Badge></CardContent></Card>
    {query.data?.suppressedGroups ? <p className="rounded-[8px] border border-accent/25 bg-accent-soft/35 px-3 py-2.5 text-xs text-[#92400e]">{query.data.suppressedGroups} group(s) suppressed because the count is below the privacy threshold.</p> : null}
    {error ? <p role="alert" className="text-sm text-danger">{error}</p> : null}
    {query.isLoading ? <Skeleton className="h-80" /> : query.error ? <EmptyState title="Report unavailable" description={query.error instanceof ApiError ? query.error.message : "Could not load report data."} action={<Button variant="secondary" onClick={() => query.refetch()} icon={<RefreshCw className="size-4" />}>Retry</Button>} /> : <Card><CardHeader><CardTitle>{REPORTS.find((item) => item.key === report)?.label}</CardTitle><CardDescription>Generated {formatDateTime(query.data?.generatedAt)} · {query.data?.dataFreshness}</CardDescription></CardHeader><CardContent className="pt-3">{items.length ? <div className="overflow-hidden rounded-[10px] border border-border"><Table><TableHeader><TableRow>{columns.map((column) => <TableHead key={column}>{titleCase(column)}</TableHead>)}</TableRow></TableHeader><TableBody>{items.map((item, index) => <TableRow key={`${displayValue(item.groupKey ?? item.programmeId ?? item.section)}-${index}`}>{columns.map((column) => <TableCell key={column} className="max-w-72 break-words text-xs">{item.suppressed === true && column === "count" ? <Badge tone="warning">Suppressed</Badge> : displayValue(item[column])}</TableCell>)}</TableRow>)}</TableBody></Table></div> : <p className="rounded-[8px] border border-dashed border-border px-4 py-8 text-center text-xs text-ink-soft">No rows are available for these filters.</p>}</CardContent></Card>}</div>;
}
