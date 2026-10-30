"use client";

import { useMemo, useState } from "react";

import { CapacityBar } from "@/components/institution/capacity-bar";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Programme } from "@/lib/types";

export function ProgrammeTable({ programmes }: { programmes: Programme[] }) {
  const [campus, setCampus] = useState("all");
  const campuses = useMemo(
    () =>
      Array.from(
        new Map(programmes.map((programme) => [programme.campusId, programme.campusName])).entries(),
      ),
    [programmes],
  );
  const filtered = programmes.filter(
    (programme) => campus === "all" || programme.campusId === campus,
  );

  if (!programmes.length) {
    return (
      <EmptyState
        title="No programmes"
        description="No active programmes are configured for this institution and academic year."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <Select
          aria-label="Filter by campus"
          value={campus}
          onChange={(event) => setCampus(event.target.value)}
          containerClassName="w-full max-w-xs"
        >
          <option value="all">All campuses</option>
          {campuses.map(([id, name]) => (
            <option key={id} value={id}>
              {name ?? id}
            </option>
          ))}
        </Select>
        <p className="text-xs text-ink-soft/70">
          {filtered.length} programme{filtered.length === 1 ? "" : "s"}
        </p>
      </div>
      <div className="overflow-hidden rounded-[12px] border border-border bg-surface shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Programme</TableHead>
              <TableHead>Campus</TableHead>
              <TableHead>Approved intake</TableHead>
              <TableHead className="min-w-64">Reported vs approved</TableHead>
              <TableHead>Approval evidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((programme) => (
              <TableRow key={programme.id}>
                <TableCell>
                  <p className="font-medium text-ink">{programme.programmeName}</p>
                  <p className="text-xs text-ink-soft/70">
                    {programme.programmeCode} · {programme.awardLevel.replaceAll("_", " ")}
                  </p>
                </TableCell>
                <TableCell className="text-sm text-ink-soft">{programme.campusName ?? "—"}</TableCell>
                <TableCell>
                  <p className="text-sm tabular text-ink">
                    {programme.approvedRegular.toLocaleString("en-IN")} regular
                  </p>
                  <p className="text-xs tabular text-ink-soft/75">
                    {programme.approvedSupernumerary.toLocaleString("en-IN")} supernumerary
                  </p>
                </TableCell>
                <TableCell>
                  <CapacityBar
                    approvedRegular={programme.approvedRegular}
                    approvedSupernumerary={programme.approvedSupernumerary}
                    reportedRegular={programme.reportedRegular}
                    reportedSupernumerary={programme.reportedSupernumerary}
                    status={programme.capacityStatus ?? "MISSING_APPROVAL_DATA"}
                  />
                </TableCell>
                <TableCell className="max-w-56">
                  <p className="break-words text-xs text-ink-soft">
                    {programme.approvalReference ?? "No active approval snapshot"}
                  </p>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
