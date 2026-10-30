import { Share2 } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function StudentSharingPage() {
  return (
    <ModulePlaceholder
      eyebrow="Student portal"
      title="Sharing"
      description="Create purpose-bound, claim-scoped verification links and revoke them at any time."
      icon={Share2}
      bullets={[
        "Choose specific claims and a stated verification purpose",
        "Short-lived links with a one-time access code",
        "See who viewed a reference and when",
        "Revoke access immediately without affecting your enrolment",
      ]}
      phase="Phase 4"
    />
  );
}
