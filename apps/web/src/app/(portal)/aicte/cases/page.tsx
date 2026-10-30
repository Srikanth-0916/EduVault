import { ClipboardCheck } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteCasesPage() {
  return (
    <ModulePlaceholder
      eyebrow="AICTE national console"
      title="Cross-institution cases"
      description="Duplicate and overlap findings requiring national evidence and a documented human resolution."
      icon={ClipboardCheck}
      bullets={[
        "Cross-institution overlap candidates with masked evidence",
        "Resolution outcomes such as valid transfer or data correction",
        "Student-visible outcome after the institution closes a case",
        "No automatic cancellation, fraud label or record merge",
      ]}
      phase="Phase 3"
    />
  );
}
