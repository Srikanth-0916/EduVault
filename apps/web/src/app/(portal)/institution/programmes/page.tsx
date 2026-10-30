import { BookOpen } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function InstitutionProgrammesPage() {
  return (
    <ModulePlaceholder
      eyebrow="Institution workspace"
      title="Programmes & intake"
      description="Read-only view of approved programmes, campuses and versioned intake snapshots set by AICTE."
      icon={BookOpen}
      bullets={[
        "Approved regular seats and separate supernumerary allocations",
        "Authorization references for special capacity",
        "Programme/year capacity evidence used by validation",
        "Institution users cannot modify approved intake",
      ]}
    />
  );
}
