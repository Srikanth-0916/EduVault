import { ScanLine } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function VerifierPage() {
  return (
    <ModulePlaceholder
      eyebrow="Verifier access"
      title="Verify a reference"
      description="Resolve a reference shared by a student. The public verification route will not expose unnecessary personal data."
      icon={ScanLine}
      bullets={[
        "Enter a reference and one-time access code",
        "Display only the claims the student authorized",
        "Show purpose, issuer and expiry alongside the result",
        "Every resolution is logged and rate-limited",
      ]}
      phase="Phase 4"
    />
  );
}
