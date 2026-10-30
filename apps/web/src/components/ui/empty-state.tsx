import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: {
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-[12px] border border-dashed border-border bg-surface/60 px-6 py-12 text-center",
        className,
      )}
    >
      {icon ? (
        <div className="flex size-11 items-center justify-center rounded-full bg-primary-soft text-primary">
          {icon}
        </div>
      ) : null}
      <div>
        <h3 className="font-display text-base font-semibold text-ink">{title}</h3>
        <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-ink-soft">{description}</p>
      </div>
      {action}
    </div>
  );
}
