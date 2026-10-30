import {
  AlertTriangle,
  BadgeCheck,
  FileClock,
  GraduationCap,
  UserRoundCheck,
  UsersRound,
} from "lucide-react";

import { StatCard } from "@/components/ui/card";
import type { Kpi } from "@/lib/types";

const ICONS = {
  approved_intake: GraduationCap,
  reported_enrollment: UsersRound,
  active_enrollment: UserRoundCheck,
  apaar_gaps: AlertTriangle,
  unresolved_cases: BadgeCheck,
  pending_batches: FileClock,
} as const;

export function KpiGrid({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      {kpis.map((kpi) => {
        const Icon = ICONS[kpi.key as keyof typeof ICONS] ?? GraduationCap;
        const tone =
          kpi.tone === "warning" || kpi.tone === "success" || kpi.tone === "danger"
            ? kpi.tone
            : "default";
        return (
          <StatCard
            key={kpi.key}
            label={kpi.label}
            value={kpi.value.toLocaleString("en-IN")}
            hint={kpi.hint ?? undefined}
            tone={tone}
            icon={<Icon className="size-4" aria-hidden="true" />}
          />
        );
      })}
    </div>
  );
}
