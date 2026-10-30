"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/nav";
import type { Role } from "@/lib/types";

const INSTITUTION_ROLES: Role[] = [
  "INSTITUTION_ADMIN",
  "INSTITUTION_OPERATOR",
  "INSTITUTION_NODAL_OFFICER",
];

export default function InstitutionLayout({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const allowed = Boolean(user?.roles.some((role) => INSTITUTION_ROLES.includes(role)));

  useEffect(() => {
    if (!isLoading && user && !allowed) {
      router.replace(roleHome(user.roles));
    }
  }, [allowed, isLoading, router, user]);

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-ink-soft" role="status">
        <Loader2 className="mr-2 size-4 animate-spin text-primary" aria-hidden="true" />
        Checking institution access…
      </div>
    );
  }
  if (!user || !allowed) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-ink-soft">
        This workspace is restricted to institution staff.
      </div>
    );
  }
  return children;
}
