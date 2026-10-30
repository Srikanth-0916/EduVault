"use client";

import { AlertCircle, ChevronDown } from "lucide-react";
import { useId, type SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  containerClassName?: string;
}

export function Select({
  label,
  hint,
  error,
  className,
  containerClassName,
  id,
  required,
  children,
  ...props
}: SelectProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const descriptionId = `${selectId}-description`;

  return (
    <div className={cn("flex flex-col gap-1.5", containerClassName)}>
      {label ? (
        <label htmlFor={selectId} className="text-[13px] font-medium text-ink">
          {label}
          {required ? (
            <span className="ml-0.5 text-danger" aria-hidden="true">
              *
            </span>
          ) : null}
        </label>
      ) : null}
      <div className="relative">
        <select
          id={selectId}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={error || hint ? descriptionId : undefined}
          className={cn(
            "h-11 w-full appearance-none rounded-[8px] border border-border bg-surface pl-3 pr-9 text-sm text-ink transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:bg-surface-muted",
            error && "border-danger/60",
            className,
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-ink-soft/60"
          aria-hidden="true"
        />
      </div>
      {error || hint ? (
        <p
          id={descriptionId}
          className={cn(
            "flex items-start gap-1.5 text-xs leading-5",
            error ? "text-danger" : "text-ink-soft/75",
          )}
        >
          {error ? <AlertCircle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" /> : null}
          {error ?? hint}
        </p>
      ) : null}
    </div>
  );
}
