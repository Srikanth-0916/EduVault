import { ChartNoAxesCombined } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteOverviewPage() {
  return (
    <ModulePlaceholder
      eyebrow="AICTE national console"
      title="National overview"
      description="Coverage, reported enrolment and quality signals across institutions, without conflating acceptance with identity verification."
      icon={ChartNoAxesCombined}
      bullets={[
        "Approved intake against reported enrolment by programme",
        "Institution submission coverage and pending review load",
        "Identity format, mock external check and acceptance distributions",
        "Drill-down links that preserve role and tenant scope",
      ]}
      phase="Phase 3"
    />
  );
}
