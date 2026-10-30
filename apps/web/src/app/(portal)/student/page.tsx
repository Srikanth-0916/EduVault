import { UserRound } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function StudentRecordPage() {
  return (
    <ModulePlaceholder
      eyebrow="Student portal"
      title="My record"
      description="Your identity, enrolment and the status of each claim about your record — explained without a single opaque “verified” badge."
      icon={UserRound}
      bullets={[
        "APAAR format validity shown separately from external checks",
        "Current enrolment and institution-reported status",
        "Open corrections and case outcomes visible to you",
        "Clear language for every status and next action",
      ]}
      phase="Phase 4"
    />
  );
}
