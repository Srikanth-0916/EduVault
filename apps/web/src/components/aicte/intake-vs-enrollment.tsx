import { BarChart } from "@/components/charts/bar-chart";
import type { DashboardCapacityRow } from "@/lib/types";

export function IntakeVsEnrollment({ rows }: { rows: DashboardCapacityRow[] }) {
  return <BarChart data={rows.slice(0, 8).map((row) => ({ key: row.programmeId, label: row.programmeCode, count: row.reportedTotal }))} emptyLabel="No possible-excess programmes." />;
}
