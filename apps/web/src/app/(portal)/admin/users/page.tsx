import { UserCog } from "lucide-react";

import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AdminUsersPage() {
  return (
    <ModulePlaceholder
      eyebrow="Platform administration"
      title="Users & access"
      description="National-level account administration with explicit, auditable role assignment."
      icon={UserCog}
      bullets={[
        "Search users across institutions without exposing credentials",
        "Assign or revoke roles with an audit reason",
        "Suspend accounts and invalidate active sessions",
        "Never surface password hashes or temporary credentials",
      ]}
      phase="Phase 5"
    />
  );
}
