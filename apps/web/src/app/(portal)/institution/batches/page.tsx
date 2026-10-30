import { FileSpreadsheet } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function InstitutionBatchesPage() {
  return (
    <ModulePlaceholder
      eyebrow="Institution workspace"
      title="Submission batches"
      description="CSV intake with staged validation, row-level findings, nodal attestation and AICTE review status."
      icon={FileSpreadsheet}
      bullets={[
        "Private CSV upload with checksum, uploader and timestamp evidence",
        "Row-level rule ID, severity, message and next action",
        "Blocking errors gate submission; warnings stay visible",
        "Nodal attestation, signed receipt and review timeline",
      ]}
    />
  );
}
