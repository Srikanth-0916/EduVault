import { ChartNoAxesCombined } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteReportsPage() {
  return (
    <ModulePlaceholder
      eyebrow="AICTE national console"
      title="Reports & reconciliation"
      description="Aggregate, privacy-reviewed exports and reconciliation views for national reporting."
      icon={ChartNoAxesCombined}
      bullets={[
        "Aggregate capacity and enrolment reports",
        "Accepted-versus-reported reconciliation with reason codes",
        "Export provenance, filter summary and row counts",
        "Small-cell suppression to reduce re-identification risk",
      ]}
      phase="Phase 3"
    />
  );
}
