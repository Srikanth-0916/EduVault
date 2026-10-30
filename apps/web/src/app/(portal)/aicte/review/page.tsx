import { ShieldCheck } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AicteReviewPage() {
  return (
    <ModulePlaceholder
      eyebrow="AICTE national console"
      title="Review queue"
      description="Submitted batches with validation evidence, capacity warnings and correction history for a human decision."
      icon={ShieldCheck}
      bullets={[
        "Filter by institution, academic year and submission age",
        "Row-level warnings alongside a batch-level decision",
        "Accept, return for correction or reject with a reason",
        "Optimistic-lock and separation-of-duties checks on submit",
      ]}
      phase="Phase 3"
    />
  );
}
