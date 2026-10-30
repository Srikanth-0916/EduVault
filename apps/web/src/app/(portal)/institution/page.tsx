import { LayoutDashboard } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function InstitutionOverviewPage() {
  return (
    <ModulePlaceholder
      eyebrow="Institution workspace"
      title="Institution overview"
      description="Approved intake, reported enrolment, identity quality and open review cases for your institution."
      icon={LayoutDashboard}
      bullets={[
        "Approved regular and separately authorized supernumerary intake",
        "Reported enrolment by programme with capacity state",
        "APAAR format, mock external check and AICTE acceptance shown separately",
        "Recent batches, unresolved cases and correction actions",
      ]}
    />
  );
}
