import { Badge } from "@/components/ui/badge";
import { ROLE_LABELS } from "@/lib/demo";
import type { Role } from "@/lib/types";

const TONE: Record<Role, "info" | "neutral" | "success" | "warning" | "ink" | "muted"> = {
  INSTITUTION_ADMIN: "info",
  INSTITUTION_OPERATOR: "info",
  INSTITUTION_NODAL_OFFICER: "info",
  AICTE_REVIEWER: "ink",
  AICTE_SUPERVISOR: "ink",
  AICTE_ANALYST: "ink",
  SYSTEM_ADMIN: "neutral",
  AUDITOR: "muted",
  STUDENT: "success",
  EXTERNAL_VERIFIER: "warning",
};

export function RoleBadge({ role, className }: { role: Role; className?: string }) {
  return (
    <Badge tone={TONE[role] ?? "neutral"} className={className}>
      {ROLE_LABELS[role] ?? role}
    </Badge>
  );
}
