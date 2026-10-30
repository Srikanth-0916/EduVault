import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/status-badge";
import type { EnrollmentSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function StudentTable({ students }: { students: EnrollmentSummary[] }) {
  if (!students.length) {
    return (
      <EmptyState
        title="No student records"
        description="No enrolments match the selected filters. Adjust the filters or add a student."
      />
    );
  }
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-surface shadow-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Student</TableHead>
            <TableHead>APAAR</TableHead>
            <TableHead>Programme</TableHead>
            <TableHead>Year</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Seat</TableHead>
            <TableHead>Acceptance</TableHead>
            <TableHead className="text-right">Updated</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student) => (
            <TableRow key={student.id}>
              <TableCell>
                <Link
                  href={`/institution/students/${student.id}`}
                  className="font-medium text-ink underline-offset-4 hover:text-primary hover:underline"
                >
                  {student.studentFullName}
                </Link>
                <p className="text-xs text-ink-soft/70">{student.studentLocalId}</p>
              </TableCell>
              <TableCell>
                <p className="font-mono text-xs text-ink">{student.maskedApaar}</p>
                <StatusBadge family="identity" status={student.identityStatus ?? "MISSING"} className="mt-1" />
              </TableCell>
              <TableCell>
                <p className="text-sm text-ink">{student.programmeName ?? "—"}</p>
                <p className="text-xs text-ink-soft/70">{student.campusName ?? "—"}</p>
              </TableCell>
              <TableCell className="text-sm tabular text-ink-soft">{student.academicYear}</TableCell>
              <TableCell>
                <StatusBadge family="enrollment" status={student.enrollmentStatus} />
              </TableCell>
              <TableCell>
                <Badge tone={student.seatClassification === "APPROVED_SUPERNUMERARY" ? "info" : "neutral"}>
                  {student.seatClassification === "APPROVED_SUPERNUMERARY" ? "Supernumerary" : "Regular"}
                </Badge>
              </TableCell>
              <TableCell>
                {student.recordAcceptedAt ? (
                  <Badge tone="success">AICTE accepted</Badge>
                ) : (
                  <span className="text-xs text-ink-soft/70">Not accepted</span>
                )}
              </TableCell>
              <TableCell className="text-right text-xs text-ink-soft">
                {formatDate(student.updatedAt)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableCaption>
          APAAR values are masked to the last four digits. Format validity, mock external checks and AICTE acceptance are separate states.
        </TableCaption>
      </Table>
    </div>
  );
}
