import { ScrollText } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteAuditPage() {
  return (
    <ModulePlaceholder
      eyebrow="Accountability"
      title="Audit trail"
      description="An append-only, masked history of security-relevant actions across the platform."
      icon={ScrollText}
      bullets={[
        "Actor, action, resource and outcome for each event",
        "Sensitive values masked before the record is written",
        "Immutable entries — no edit or delete endpoints",
        "Filter by actor, institution, action and time window",
      ]}
      phase="Phase 3"
    />
  );
}
