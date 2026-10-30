import { StatusBadge } from "@/components/status-badge";

export function IdentityStatus({
  status,
  verifiedAt,
}: {
  status: string;
  verifiedAt?: string | null;
}) {
  const formatOnly = status === "FORMAT_VALID";
  return (
    <div className="space-y-1">
      <StatusBadge family="identity" status={status} />
      <p className="text-[11px] leading-4 text-ink-soft/75">
        {formatOnly
          ? "Format is valid only; no external confirmation."
          : status === "EXTERNALLY_CONFIRMED"
            ? `Mock external check${verifiedAt ? ` · ${verifiedAt}` : ""}. Not a live government response.`
            : status === "EXTERNAL_MISMATCH"
              ? "Mock external check returned a mismatch. Review required."
              : "External check has not confirmed this identifier."}
      </p>
    </div>
  );
}
