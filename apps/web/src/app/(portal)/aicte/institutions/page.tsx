import { Building2 } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteInstitutionsPage() {
  return (
    <ModulePlaceholder
      eyebrow="AICTE national console"
      title="Institutions"
      description="Institution master data, campuses, programmes and versioned approved intake snapshots."
      icon={Building2}
      bullets={[
        "Institution and campus directory with deterministic demo IDs",
        "Programme approvals, regular seats and authorized allocations",
        "Snapshot versions with effective dates and references",
        "Read-only access for auditors and analysts",
      ]}
      phase="Phase 2"
    />
  );
}
