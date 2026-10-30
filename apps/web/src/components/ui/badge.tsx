import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export type BadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "muted"
  | "mock"
  | "ink";

const toneStyles: Record<BadgeTone, string> = {
  neutral: "border-border bg-surface-muted text-ink-soft",
  info: "border-[#99d5cf] bg-primary-soft text-[#115e59]",
  success: "border-[#a7e3b9] bg-success-soft text-[#166534]",
  warning: "border-[#f1d28a] bg-accent-soft text-[#92400e]",
  danger: "border-[#f3b5b0] bg-danger-soft text-[#991b1b]",
  muted: "border-border bg-transparent text-ink-soft/70",
  mock: "border-dashed border-accent/40 bg-accent-soft/70 text-[#92400e]",
  ink: "border-ink/10 bg-ink text-white",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  icon?: ReactNode;
}

export function Badge({ className, tone = "neutral", icon, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold leading-5 tracking-wide whitespace-nowrap",
        toneStyles[tone],
        className,
      )}
      {...props}
    >
      {icon}
      {children}
    </span>
  );
}
