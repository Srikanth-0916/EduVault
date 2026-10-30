import { Activity, AlertTriangle, Building2, ClipboardCheck, FileClock, Layers3, Scale, UsersRound } from "lucide-react";

import { StatCard } from "@/components/ui/card";
import type { Kpi } from "@/lib/types";

const ICONS = [Building2, UsersRound, Activity, FileClock, AlertTriangle, Scale, Building2, Layers3];

export function NationalKpiGrid({ kpis }: { kpis: Kpi[] }) {
  return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8">{kpis.map((kpi, index) => { const Icon = ICONS[index] ?? ClipboardCheck; return <StatCard key={kpi.key} label={kpi.label} value={kpi.value.toLocaleString("en-IN")} hint={kpi.hint ?? undefined} tone={kpi.tone === "warning" || kpi.tone === "success" || kpi.tone === "danger" ? kpi.tone : "default"} icon={<Icon className="size-4" aria-hidden="true" />} />; })}</div>;
}
