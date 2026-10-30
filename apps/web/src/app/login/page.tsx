"use client";

import {
  ArrowRight,
  Eye,
  EyeOff,
  KeyRound,
  ListChecks,
  Loader2,
  ShieldCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Logo } from "@/components/logo";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { DEMO_ACCOUNTS, DEMO_PASSWORD } from "@/lib/demo";
import { roleHome } from "@/lib/nav";
import { cn } from "@/lib/utils";

const PROOF_POINTS = [
  {
    icon: ShieldCheck,
    title: "Tenant-isolated by default",
    body: "Every record lookup is scoped to the signed-in institution or an authorized national role.",
  },
  {
    icon: ListChecks,
    title: "Explainable rules, not black boxes",
    body: "Validation findings carry a rule ID, severity, evidence and a plain-language next action.",
  },
  {
    icon: KeyRound,
    title: "Student-controlled disclosure",
    body: "Optional verification links are purpose-bound, claim-scoped, expiring and revocable.",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading, login } = useAuth();
  const [email, setEmail] = useState("operator@demo-ait.edu");
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(roleHome(user.roles));
    }
  }, [isLoading, user, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const signedIn = await login(email.trim(), password);
      router.replace(roleHome(signedIn.roles));
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Sign-in failed. Check that the API service is running.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function chooseAccount(accountEmail: string) {
    setEmail(accountEmail);
    setPassword(DEMO_PASSWORD);
    setError(null);
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100dvh-2rem)] items-center justify-center bg-canvas">
        <div className="flex items-center gap-2 text-sm text-ink-soft" role="status">
          <Loader2 className="size-4 animate-spin text-primary" aria-hidden="true" />
          Restoring demo session…
        </div>
      </div>
    );
  }

  if (user) return null;

  return (
    <div className="grid min-h-[calc(100dvh-2rem)] bg-canvas lg:grid-cols-[1.03fr_0.97fr]">
      <section className="relative hidden overflow-hidden bg-ink p-10 text-white lg:flex xl:p-14">
        <div className="ink-grid absolute inset-0 opacity-80" aria-hidden="true" />
        <div
          className="absolute -right-32 top-1/4 size-96 rounded-full bg-primary/20 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative z-10 flex w-full flex-col">
          <Logo variant="light" />
          <div className="my-auto max-w-xl py-12">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#5eead4]">
              APAAR student data management &amp; verification
            </p>
            <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.08] tracking-[-0.03em] text-white xl:text-[52px]">
              A trustworthy record of every student journey.
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-7 text-white/62">
              Approved intake, institution submissions, human review and
              purpose-bound verification — in one accountable workflow. Built as
              a synthetic-data prototype.
            </p>

            <ul className="mt-10 space-y-5">
              {PROOF_POINTS.map(({ icon: Icon, title, body }) => (
                <li key={title} className="flex gap-3.5">
                  <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-[9px] border border-white/10 bg-white/[0.06] text-[#5eead4]">
                    <Icon className="size-4" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="block text-[13px] font-semibold text-white/90">{title}</span>
                    <span className="mt-0.5 block max-w-md text-xs leading-5 text-white/48">
                      {body}
                    </span>
                  </span>
                </li>
              ))}
            </ul>

            <div className="mt-10 max-w-lg rounded-[14px] border border-white/10 bg-white/[0.04] p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-white/55">
                One record, distinct claims
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <StatusBadge family="identity" status="FORMAT_VALID" />
                <StatusBadge family="mock" status="MOCK" />
                <StatusBadge family="batch" status="ACCEPTED" />
              </div>
              <p className="mt-3 text-xs leading-5 text-white/42">
                Format validity, external check status and AICTE acceptance stay
                separate. The prototype never collapses them into a single
                “verified” badge.
              </p>
            </div>
          </div>
          <p className="text-[10px] leading-5 text-white/34">
            Prototype only · Synthetic data · Mock/sandbox integrations · Not an
            AICTE production system
          </p>
        </div>
      </section>

      <main className="flex items-center justify-center px-4 py-10 sm:px-8 lg:py-14">
        <div className="w-full max-w-[430px]">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
            Demo workspace
          </p>
          <h2 className="mt-1.5 font-display text-3xl font-semibold tracking-tight text-ink">
            Sign in to continue
          </h2>
          <p className="mt-2 text-sm leading-6 text-ink-soft">
            Use a seeded role account. The password is shared across demo users
            and prefilled for convenience.
          </p>

          {error ? (
            <div
              role="alert"
              className="mt-5 rounded-[10px] border border-danger/20 bg-danger-soft/70 px-3.5 py-3 text-sm leading-6 text-danger"
            >
              {error}
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <Input
              label="Work email"
              type="email"
              name="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@institution.edu"
              required
            />
            <Input
              label="Password"
              type={showPassword ? "text" : "password"}
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              trailing={
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="inline-flex size-9 items-center justify-center rounded-[6px] text-ink-soft/60 hover:bg-surface-muted hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="size-4" aria-hidden="true" />
                  ) : (
                    <Eye className="size-4" aria-hidden="true" />
                  )}
                </button>
              }
            />
            <Button
              type="submit"
              fullWidth
              size="lg"
              loading={submitting}
              icon={!submitting ? <ArrowRight className="size-4" aria-hidden="true" /> : undefined}
            >
              {submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="mt-7">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink-soft/65">
                Demo accounts
              </p>
              <p className="text-[11px] text-ink-soft/55">Password: {DEMO_PASSWORD}</p>
            </div>
            <div className="mt-2.5 grid max-h-[250px] grid-cols-2 gap-2 overflow-y-auto pr-1 scrollbar-thin">
              {DEMO_ACCOUNTS.map((account) => {
                const selected = account.email === email;
                return (
                  <button
                    key={account.email}
                    type="button"
                    onClick={() => chooseAccount(account.email)}
                    aria-pressed={selected}
                    className={cn(
                      "rounded-[8px] border px-2.5 py-2 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
                      selected
                        ? "border-primary/35 bg-primary-soft/55"
                        : "border-border bg-surface hover:border-ink/20 hover:bg-surface-muted/50",
                    )}
                  >
                    <span className="block text-[11px] font-semibold text-ink">
                      {account.label}
                    </span>
                    <span className="mt-0.5 block truncate text-[10px] text-ink-soft/60">
                      {account.scope} · {account.email}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <p className="mt-6 border-t border-border pt-4 text-[10px] leading-5 text-ink-soft/55">
            This portal contains synthetic records only. APAAR checks are served
            by a mock adapter and must never be read as live government
            verification. See the repository documentation for limitations.
          </p>
        </div>
      </main>
    </div>
  );
}
