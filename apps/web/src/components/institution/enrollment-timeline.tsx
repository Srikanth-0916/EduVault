import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { EnrollmentVersion } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

export function EnrollmentTimeline({ versions }: { versions: EnrollmentVersion[] }) {
  if (!versions.length) {
    return <EmptyState title="No versions" description="No version snapshots are recorded for this enrolment." />;
  }
  return (
    <ol className="relative space-y-4 border-l border-border pl-5">
      {versions.map((version) => (
        <li key={version.id} className="relative">
          <span
            className="absolute -left-[26px] top-1.5 size-2.5 rounded-full border-2 border-surface bg-primary"
            aria-hidden="true"
          />
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-ink">Version {version.version}</p>
            <Badge tone="neutral">{titleCase(version.actorRole ?? "system")}</Badge>
          </div>
          <p className="mt-0.5 text-xs text-ink-soft/75">
            {formatDateTime(version.createdAt)} · {version.changeReason ?? "Record snapshot"}
          </p>
          <dl className="mt-2 grid gap-x-4 gap-y-1 text-xs sm:grid-cols-2">
            <div className="flex gap-1.5">
              <dt className="text-ink-soft/70">Name</dt>
              <dd className="truncate text-ink">{String(version.snapshot.studentName ?? "—")}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-ink-soft/70">APAAR</dt>
              <dd className="font-mono text-ink">{String(version.snapshot.maskedApaar ?? "—")}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-ink-soft/70">Status</dt>
              <dd className="text-ink">{titleCase(String(version.snapshot.enrollmentStatus ?? "—"))}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-ink-soft/70">Seat</dt>
              <dd className="text-ink">{titleCase(String(version.snapshot.seatClassification ?? "—"))}</dd>
            </div>
          </dl>
        </li>
      ))}
    </ol>
  );
}
