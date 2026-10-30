import { ClipboardCheck } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function InstitutionCasesPage() {
  return (
    <ModulePlaceholder
      eyebrow="Institution workspace"
      title="Cases"
      description="Duplicate and overlap findings that need human evidence and a documented resolution."
      icon={ClipboardCheck}
      bullets={[
        "Same-institution and cross-institution overlap cases",
        "Masked evidence with dates, institutions and overlap days",
        "Resolution codes such as valid transfer or data error",
        "No automatic fraud finding, cancellation or record merge",
      ]}
    />
  );
}
