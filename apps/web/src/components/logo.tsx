import { cn } from "@/lib/utils";

export function Logo({
  variant = "dark",
  compact = false,
  className,
}: {
  variant?: "dark" | "light";
  compact?: boolean;
  className?: string;
}) {
  const isLight = variant === "light";
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "relative flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-[10px] border",
          isLight
            ? "border-white/15 bg-white/10 text-white"
            : "border-primary/15 bg-ink text-white",
        )}
        aria-hidden="true"
      >
        <svg viewBox="0 0 32 32" className="size-5" fill="none">
          <path
            d="M7 23.5 14.1 9h3.8L25 23.5h-4.3l-1.2-2.9h-7L11.2 23.5H7Zm6.6-6.2h4.7L16 12.4l-2.4 4.9Z"
            fill="currentColor"
          />
          <circle cx="25.5" cy="7" r="2.2" fill="#5eead4" />
        </svg>
      </span>
      {!compact ? (
        <span className="min-w-0">
          <span
            className={cn(
              "block font-display text-sm font-semibold leading-tight tracking-tight",
              isLight ? "text-white" : "text-ink",
            )}
          >
            APAAR-SDMV
          </span>
          <span
            className={cn(
              "block text-[10px] font-medium uppercase tracking-[0.14em]",
              isLight ? "text-white/55" : "text-ink-soft/60",
            )}
          >
            Student data platform
          </span>
        </span>
      ) : null}
    </div>
  );
}
