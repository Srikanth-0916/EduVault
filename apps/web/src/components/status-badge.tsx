import { FlaskConical } from "lucide-react";

import { Badge, type BadgeTone } from "@/components/ui/badge";
import { titleCase, cn } from "@/lib/utils";

export type StatusFamily =
  | "identity"
  | "batch"
  | "capacity"
  | "severity"
  | "case"
  | "verification"
  | "enrollment"
  | "user"
  | "mock"
  | "role";

interface StatusMeta {
  label: string;
  tone: BadgeTone;
}

const STATUS: Record<Exclude<StatusFamily, "mock" | "role">, Record<string, StatusMeta>> = {
  identity: {
    MISSING: { label: "APAAR missing", tone: "muted" },
    MALFORMED: { label: "APAAR malformed", tone: "danger" },
    FORMAT_VALID: { label: "Format valid", tone: "info" },
    PENDING_EXTERNAL_CHECK: { label: "Pending mock check", tone: "warning" },
    EXTERNALLY_CONFIRMED: { label: "Externally confirmed (mock)", tone: "success" },
    EXTERNAL_MISMATCH: { label: "External mismatch (mock)", tone: "danger" },
    EXTERNAL_UNAVAILABLE: { label: "External unavailable (mock)", tone: "neutral" },
    MANUAL_REVIEW: { label: "Manual review", tone: "warning" },
    CORRECTED: { label: "Corrected", tone: "info" },
  },
  batch: {
    DRAFT: { label: "Draft", tone: "neutral" },
    VALIDATING: { label: "Validating", tone: "info" },
    VALIDATION_FAILED: { label: "Validation failed", tone: "danger" },
    READY_FOR_ATTESTATION: { label: "Ready for attestation", tone: "warning" },
    SUBMITTED: { label: "Submitted", tone: "info" },
    UNDER_AICTE_REVIEW: { label: "Under AICTE review", tone: "info" },
    RETURNED_FOR_CORRECTION: { label: "Returned for correction", tone: "warning" },
    ACCEPTED: { label: "Accepted by AICTE", tone: "success" },
    REJECTED: { label: "Rejected", tone: "danger" },
  },
  capacity: {
    WITHIN_APPROVED_INTAKE: { label: "Within approved intake", tone: "success" },
    WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY: {
      label: "Within approved + authorized",
      tone: "info",
    },
    POSSIBLE_EXCESS: { label: "Possible excess", tone: "warning" },
    MISSING_APPROVAL_DATA: { label: "Missing approval data", tone: "neutral" },
    PENDING_RULE_REVIEW: { label: "Pending rule review", tone: "warning" },
  },
  severity: {
    INFO: { label: "Info", tone: "neutral" },
    LOW: { label: "Low", tone: "neutral" },
    WARNING: { label: "Warning", tone: "warning" },
    HIGH: { label: "High", tone: "danger" },
    CRITICAL: { label: "Critical", tone: "danger" },
  },
  case: {
    OPEN: { label: "Open", tone: "warning" },
    IN_REVIEW: { label: "In review", tone: "info" },
    RESOLVED: { label: "Resolved", tone: "success" },
    WITHDRAWN: { label: "Withdrawn", tone: "neutral" },
  },
  verification: {
    PENDING_AUTHORIZATION: { label: "Pending authorization", tone: "warning" },
    AUTHORIZED: { label: "Authorized", tone: "info" },
    VIEWED: { label: "Viewed", tone: "info" },
    CONSUMED: { label: "Consumed", tone: "success" },
    EXPIRED: { label: "Expired", tone: "neutral" },
    REVOKED: { label: "Revoked", tone: "danger" },
  },
  enrollment: {
    PENDING: { label: "Pending", tone: "warning" },
    ACTIVE: { label: "Active", tone: "success" },
    WITHDRAWN: { label: "Withdrawn", tone: "neutral" },
    TRANSFERRED: { label: "Transferred", tone: "info" },
    COMPLETED: { label: "Completed", tone: "success" },
    CANCELLED: { label: "Cancelled", tone: "danger" },
    UNDER_REVIEW: { label: "Under review", tone: "warning" },
  },
  user: {
    PENDING_INVITATION: { label: "Pending invitation", tone: "warning" },
    ACTIVE: { label: "Active", tone: "success" },
    SUSPENDED: { label: "Suspended", tone: "danger" },
  },
};

export function getStatusMeta(family: StatusFamily, status: string): StatusMeta {
  if (family === "mock") return { label: "Mock/sandbox", tone: "mock" };
  if (family === "role") return { label: titleCase(status), tone: "neutral" };
  const table = STATUS[family];
  return table[status] ?? { label: titleCase(status), tone: "neutral" };
}

export function StatusBadge({
  family,
  status,
  label,
  className,
}: {
  family: StatusFamily;
  status: string;
  label?: string;
  className?: string;
}) {
  const meta = getStatusMeta(family, status);
  return (
    <Badge
      tone={meta.tone}
      className={cn(family === "mock" && "gap-1", className)}
      data-status-family={family}
      data-status={status}
    >
      {family === "mock" ? <FlaskConical className="size-3" aria-hidden="true" /> : null}
      {label ?? meta.label}
    </Badge>
  );
}
