"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/nav";

export default function StudentLayout({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const allowed = Boolean(user?.roles.includes("STUDENT"));
  useEffect(() => { if (!isLoading && user && !allowed) router.replace(roleHome(user.roles)); }, [allowed, isLoading, router, user]);
  if (isLoading) return <div className="flex min-h-[40vh] items-center justify-center text-sm text-ink-soft"><Loader2 className="mr-2 size-4 animate-spin text-primary" />Checking student access…</div>;
  if (!user || !allowed) return <div className="flex min-h-[40vh] items-center justify-center text-sm text-ink-soft">Student access is required.</div>;
  return children;
}
