import { CheckCircle2, Construction, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ModulePlaceholder({
  eyebrow,
  title,
  description,
  icon: Icon = Construction,
  bullets,
  phase = "Phase 2",
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon?: LucideIcon;
  bullets: string[];
  phase?: string;
  action?: ReactNode;
}) {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          <>
            {action}
            <Badge tone="warning">{phase} module</Badge>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="overflow-hidden">
          <div className="h-1 w-full bg-primary/70" aria-hidden="true" />
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <span className="flex size-11 shrink-0 items-center justify-center rounded-[10px] bg-primary-soft text-primary">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <div>
                <h2 className="font-display text-lg font-semibold text-ink">
                  Module arriving in {phase}
                </h2>
                <p className="mt-1.5 max-w-2xl text-sm leading-6 text-ink-soft">
                  The role-aware shell, session handling and design system are
                  live. This module is intentionally a placeholder until its
                  API and workflow surface lands in the next phase.
                </p>
              </div>
            </div>

            <ul className="mt-6 grid gap-2.5 sm:grid-cols-2">
              {bullets.map((bullet) => (
                <li
                  key={bullet}
                  className="flex items-start gap-2 rounded-[8px] border border-border bg-surface-muted/35 px-3 py-2.5 text-xs leading-5 text-ink-soft"
                >
                  <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
                  {bullet}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>What this shell already proves</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-3 text-xs leading-5 text-ink-soft">
            <p className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
              Institution, AICTE, student and verifier navigation is resolved
              from live memberships, not client-side role guessing.
            </p>
            <p className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
              Unauthenticated visitors are redirected to sign-in; expired or
              revoked roles are revalidated by the API on every request.
            </p>
            <p className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
              The shell is keyboard operable, responsive, and labels synthetic
              data and mock integrations on every screen.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
