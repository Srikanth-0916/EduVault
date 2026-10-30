import { Users } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function InstitutionStudentsPage() {
  return (
    <ModulePlaceholder
      eyebrow="Institution workspace"
      title="Students & enrolments"
      description="A tenant-scoped student register with masked APAAR values, enrolment state and correction history."
      icon={Users}
      bullets={[
        "Search and filter by academic year, programme and enrolment status",
        "Masked APAAR with format status kept distinct from external checks",
        "Record detail with version history, findings and provenance",
        "Correction workflow for returned or accepted records",
      ]}
    />
  );
}
