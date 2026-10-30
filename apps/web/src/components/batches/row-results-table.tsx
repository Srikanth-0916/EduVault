"use client";

import { Edit3, ExternalLink, FileWarning } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { BatchDetail, BatchRow, Finding } from "@/lib/types";

function RowFinding({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-[8px] border border-border bg-surface-muted/35 px-2.5 py-2">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="font-mono text-[10px] text-ink-soft">{finding.ruleId}</span>
        <StatusBadge family="severity" status={finding.severity} />
        {finding.blocking ? <Badge tone="danger">Blocking</Badge> : <Badge tone="neutral">Advisory</Badge>}
      </div>
      <p className="mt-1 text-xs leading-5 text-ink">{finding.message}</p>
      {finding.evidence?.valueMasked ? (
        <p className="mt-1 font-mono text-[10px] text-ink-soft/70">
          Evidence: {String(finding.evidence.valueMasked)}
        </p>
      ) : null}
    </div>
  );
}

export function RowResultsTable({
  batch,
  canEdit,
  onEdit,
}: {
  batch: BatchDetail;
  canEdit: boolean;
  onEdit: (row: BatchRow, values: Record<string, string>) => Promise<void>;
}) {
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return batch.rows.filter((row) => {
      const statusMatch = status === "all" || row.rowStatus === status;
      const searchMatch =
        !term ||
        row.studentName?.toLowerCase().includes(term) ||
        row.studentLocalId?.toLowerCase().includes(term) ||
        row.maskedApaar.toLowerCase().includes(term);
      return statusMatch && searchMatch;
    });
  }, [batch.rows, search, status]);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_180px]">
        <Input
          aria-label="Search batch rows"
          placeholder="Search name, student ID or masked APAAR"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Select aria-label="Filter rows by status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">All row states</option>
          <option value="VALID">Valid</option>
          <option value="WARNING">Warning</option>
          <option value="ERROR">Error</option>
          <option value="PENDING">Pending</option>
        </Select>
      </div>
      <div className="overflow-hidden rounded-[12px] border border-border bg-surface shadow-card">
        <Table>
          <TableHead className="sr-only">Batch row results</TableHead>
          <TableHeader>
            <TableRow>
              <TableHead>Row</TableHead>
              <TableHead>Student</TableHead>
              <TableHead>APAAR</TableHead>
              <TableHead>Result</TableHead>
              <TableHead className="min-w-72">Findings</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell className="font-mono text-xs text-ink-soft/70">{row.sourceRowNumber}</TableCell>
                <TableCell>
                  <p className="font-medium text-ink">{row.studentName ?? "Unnamed row"}</p>
                  <p className="text-xs text-ink-soft/70">{row.studentLocalId ?? "No institution ID"}</p>
                </TableCell>
                <TableCell className="font-mono text-xs text-ink">{row.maskedApaar}</TableCell>
                <TableCell>
                  <StatusBadge
                    family={row.rowStatus === "ERROR" ? "severity" : "batch"}
                    status={row.rowStatus === "ERROR" ? "HIGH" : row.rowStatus}
                    label={row.rowStatus === "ERROR" ? "Error" : row.rowStatus}
                  />
                </TableCell>
                <TableCell>
                  {row.findings.length ? (
                    <div className="space-y-2">
                      {row.findings.slice(0, 3).map((finding) => (
                        <RowFinding key={finding.id} finding={finding} />
                      ))}
                      {row.findings.length > 3 ? (
                        <p className="text-[11px] text-ink-soft/70">+ {row.findings.length - 3} more finding(s)</p>
                      ) : null}
                    </div>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs text-success">
                      <FileWarning className="size-3.5" aria-hidden="true" /> No findings
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1.5">
                    {row.enrollmentId ? (
                      <Link href={`/institution/students/${row.enrollmentId}`}>
                        <Button variant="ghost" size="sm" icon={<ExternalLink className="size-3.5" />}>
                          Record
                        </Button>
                      </Link>
                    ) : null}
                    {canEdit && (batch.status === "RETURNED_FOR_CORRECTION" || batch.status === "VALIDATION_FAILED" || batch.status === "DRAFT") ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<Edit3 className="size-3.5" />}
                        onClick={() =>
                          onEdit(row, {
                            studentName: row.studentName ?? "",
                            studentLocalId: row.studentLocalId ?? "",
                          })
                        }
                      >
                        Edit
                      </Button>
                    ) : null}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!rows.length ? (
          <p className="px-4 py-8 text-center text-xs text-ink-soft">No rows match the current filter.</p>
        ) : null}
      </div>
    </div>
  );
}
