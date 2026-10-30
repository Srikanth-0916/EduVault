"use client";

import { AlertCircle } from "lucide-react";
import { useId, type InputHTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leading?: ReactNode;
  trailing?: ReactNode;
  containerClassName?: string;
}

export function Input({
  label,
  hint,
  error,
  leading,
  trailing,
  className,
  containerClassName,
  id,
  required,
  ...props
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = `${inputId}-description`;
  const hasDescription = Boolean(error || hint);

  return (
    <div className={cn("flex flex-col gap-1.5", containerClassName)}>
      {label ? (
        <label htmlFor={inputId} className="text-[13px] font-medium text-ink">
          {label}
          {required ? (
            <span className="ml-0.5 text-danger" aria-hidden="true">
              *
            </span>
          ) : null}
        </label>
      ) : null}
      <div className="relative">
        {leading ? (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-ink-soft/60">
            {leading}
          </span>
        ) : null}
        <input
          id={inputId}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={hasDescription ? descriptionId : undefined}
          className={cn(
            "h-11 w-full rounded-[8px] border bg-surface px-3 text-sm text-ink shadow-[0_1px_1px_rgb(11_31_51/0.02)] transition-colors placeholder:text-ink-soft/40 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-ink-soft/60",
            leading && "pl-9",
            trailing && "pr-11",
            error ? "border-danger/60" : "border-border",
            className,
          )}
          {...props}
        />
        {trailing ? (
          <span className="absolute inset-y-0 right-1 flex items-center">{trailing}</span>
        ) : null}
      </div>
      {hasDescription ? (
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

export function Textarea({
  label,
  hint,
  error,
  className,
  containerClassName,
  id,
  required,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: string;
  hint?: string;
  error?: string;
  containerClassName?: string;
}) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = `${inputId}-description`;

  return (
    <div className={cn("flex flex-col gap-1.5", containerClassName)}>
      {label ? (
        <label htmlFor={inputId} className="text-[13px] font-medium text-ink">
          {label}
          {required ? (
            <span className="ml-0.5 text-danger" aria-hidden="true">
              *
            </span>
          ) : null}
        </label>
      ) : null}
      <textarea
        id={inputId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? descriptionId : undefined}
        className={cn(
          "min-h-24 w-full resize-y rounded-[8px] border border-border bg-surface px-3 py-2.5 text-sm text-ink transition-colors placeholder:text-ink-soft/40 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20",
          error && "border-danger/60",
          className,
        )}
        {...props}
      />
      {error || hint ? (
        <p id={descriptionId} className={cn("text-xs leading-5", error ? "text-danger" : "text-ink-soft/75")}>
          {error ?? hint}
        </p>
      ) : null}
    </div>
  );
}
